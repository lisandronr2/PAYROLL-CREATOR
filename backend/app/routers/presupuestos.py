from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.engine.presupuesto import LineaPersonalInput, calcular_linea_personal, calcular_totales_presupuesto
from app.engine.repositorio import obtener_datos_convenio_categoria, obtener_parametros_cotizacion
from app.models.convenio import CategoriaProfesional
from app.models.parametro_negocio import ParametroNegocio
from app.models.presupuesto import Presupuesto, PresupuestoLineaOtroCoste, PresupuestoLineaPersonal
from app.pdf.generador_presupuesto import generar_pdf_presupuesto
from app.schemas.presupuesto import PresupuestoCreate, PresupuestoOut

router = APIRouter(prefix="/presupuestos", tags=["presupuestos"], dependencies=[Depends(get_current_usuario)])


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"))


def _valor_negocio(db: Session, clave: str) -> Decimal:
    parametro = db.query(ParametroNegocio).filter(ParametroNegocio.clave == clave).first()
    if parametro is None:
        raise HTTPException(status_code=500, detail=f"Parámetro de negocio no configurado: {clave}")
    return Decimal(parametro.valor)


def _calcular_y_poblar(presupuesto: Presupuesto, payload: PresupuestoCreate, db: Session) -> None:
    en_fecha: date = payload.fecha

    coste_directo_personal = Decimal("0")
    lineas_personal_calculadas = []
    for linea_in in payload.lineas_personal:
        categoria = db.get(CategoriaProfesional, linea_in.categoria_id)
        if categoria is None:
            raise HTTPException(status_code=404, detail=f"Categoría {linea_in.categoria_id} no encontrada")

        try:
            datos_convenio = obtener_datos_convenio_categoria(
                db,
                linea_in.categoria_id,
                payload.empresa_id,
                en_fecha,
                jornada_porcentaje=linea_in.jornada_porcentaje,
                complemento_mensual=linea_in.complemento_mensual,
                pagas_extra_prorrateadas=linea_in.pagas_extra_prorrateadas,
            )
            parametros = obtener_parametros_cotizacion(db, en_fecha, categoria.grupo_cotizacion, "indefinido")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        entrada = LineaPersonalInput(
            cantidad_personas=linea_in.cantidad_personas,
            dias_dedicacion=linea_in.dias_dedicacion,
            numero_medias_dietas=linea_in.numero_medias_dietas,
            numero_dietas_completas_cortas=linea_in.numero_dietas_completas_cortas,
            numero_dietas_completas_largas=linea_in.numero_dietas_completas_largas,
        )
        resultado_linea = calcular_linea_personal(datos_convenio, parametros, entrada, en_fecha.year, en_fecha.month)
        coste_directo_personal += resultado_linea.coste_total_linea
        lineas_personal_calculadas.append((linea_in, resultado_linea))

    coste_directo_otros = Decimal("0")
    lineas_otros_calculadas = []
    for otro_in in payload.lineas_otros:
        importe = _q(otro_in.cantidad * otro_in.precio_unitario)
        coste_directo_otros += importe
        lineas_otros_calculadas.append((otro_in, importe))

    margen_pct = (
        payload.margen_beneficio_pct
        if payload.margen_beneficio_pct is not None
        else _valor_negocio(db, "margen_beneficio_pct_defecto")
    )
    gastos_pct = (
        payload.gastos_generales_pct
        if payload.gastos_generales_pct is not None
        else _valor_negocio(db, "gastos_generales_pct_defecto")
    )
    iva_pct = (
        payload.iva_pct if payload.iva_pct is not None else _valor_negocio(db, "iva_pct_defecto")
    )

    totales = calcular_totales_presupuesto(coste_directo_personal, coste_directo_otros, gastos_pct, margen_pct, iva_pct)

    presupuesto.empresa_id = payload.empresa_id
    presupuesto.convenio_id = payload.convenio_id
    presupuesto.nombre = payload.nombre
    presupuesto.cliente_nombre = payload.cliente_nombre
    presupuesto.cliente_nif = payload.cliente_nif
    presupuesto.fecha = payload.fecha
    presupuesto.notas = payload.notas
    presupuesto.margen_beneficio_pct = margen_pct
    presupuesto.gastos_generales_pct = gastos_pct
    presupuesto.iva_pct = iva_pct
    presupuesto.coste_directo_personal = totales.coste_directo_personal
    presupuesto.coste_directo_otros = totales.coste_directo_otros
    presupuesto.coste_directo_total = totales.coste_directo_total
    presupuesto.gastos_generales_importe = totales.gastos_generales_importe
    presupuesto.coste_total = totales.coste_total
    presupuesto.margen_importe = totales.margen_importe
    presupuesto.precio_venta = totales.precio_venta
    presupuesto.iva_importe = totales.iva_importe
    presupuesto.precio_total_cliente = totales.precio_total_cliente

    db.add(presupuesto)
    db.flush()

    presupuesto.lineas_personal.clear()
    for linea_in, resultado_linea in lineas_personal_calculadas:
        db.add(
            PresupuestoLineaPersonal(
                presupuesto_id=presupuesto.id,
                categoria_id=linea_in.categoria_id,
                cantidad_personas=linea_in.cantidad_personas,
                jornada_porcentaje=linea_in.jornada_porcentaje,
                dias_dedicacion=linea_in.dias_dedicacion,
                pagas_extra_prorrateadas=linea_in.pagas_extra_prorrateadas,
                complemento_mensual=linea_in.complemento_mensual,
                numero_medias_dietas=linea_in.numero_medias_dietas,
                numero_dietas_completas_cortas=linea_in.numero_dietas_completas_cortas,
                numero_dietas_completas_largas=linea_in.numero_dietas_completas_largas,
                coste_unitario=resultado_linea.coste_unitario,
                coste_total_linea=resultado_linea.coste_total_linea,
            )
        )

    presupuesto.lineas_otros.clear()
    for otro_in, importe in lineas_otros_calculadas:
        db.add(
            PresupuestoLineaOtroCoste(
                presupuesto_id=presupuesto.id,
                concepto=otro_in.concepto,
                cantidad=otro_in.cantidad,
                precio_unitario=otro_in.precio_unitario,
                importe=importe,
            )
        )


@router.post("", response_model=PresupuestoOut, status_code=201)
def crear_presupuesto(payload: PresupuestoCreate, db: Session = Depends(get_db)):
    presupuesto = Presupuesto()
    _calcular_y_poblar(presupuesto, payload, db)
    db.commit()
    db.refresh(presupuesto)
    return presupuesto


@router.get("", response_model=list[PresupuestoOut])
def listar_presupuestos(db: Session = Depends(get_db)):
    return db.query(Presupuesto).order_by(Presupuesto.creado_en.desc()).all()


@router.get("/{presupuesto_id}", response_model=PresupuestoOut)
def obtener_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return presupuesto


@router.put("/{presupuesto_id}", response_model=PresupuestoOut)
def actualizar_presupuesto(presupuesto_id: int, payload: PresupuestoCreate, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    _calcular_y_poblar(presupuesto, payload, db)
    db.commit()
    db.refresh(presupuesto)
    return presupuesto


@router.delete("/{presupuesto_id}", status_code=204)
def eliminar_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    db.delete(presupuesto)
    db.commit()


@router.get("/{presupuesto_id}/pdf")
def descargar_pdf_presupuesto(presupuesto_id: int, tipo: str = "cliente", db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if tipo not in ("cliente", "interno"):
        raise HTTPException(status_code=422, detail="El parámetro 'tipo' debe ser 'cliente' o 'interno'")

    ruta_pdf = generar_pdf_presupuesto(presupuesto, tipo=tipo)
    nombre_archivo = f"presupuesto_{presupuesto.id}_{tipo}.pdf"
    return FileResponse(ruta_pdf, media_type="application/pdf", filename=nombre_archivo)
