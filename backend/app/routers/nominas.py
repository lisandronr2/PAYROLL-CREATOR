from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.models.contrato import Contrato
from app.models.nomina import Nomina, NominaLinea
from app.schemas.nomina import GenerarNominaRequest, NominaOut
from app.engine.calculo import calcular_nomina
from app.engine.tipos import EventosMes
from app.engine.repositorio import (
    obtener_datos_convenio_contrato,
    obtener_parametros_cotizacion,
    obtener_tramos_irpf,
)
from app.pdf.generador import generar_pdf_nomina

router = APIRouter(prefix="/nominas", tags=["nominas"], dependencies=[Depends(get_current_usuario)])


def _calcular_y_poblar(nomina: Nomina, payload: GenerarNominaRequest, db: Session) -> None:
    """Recalcula la nómina completa (devengos, cotizaciones, IRPF) y actualiza
    los campos de `nomina` en sitio (sin insertarla ni hacer commit todavía)."""
    contrato = db.get(Contrato, payload.contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    en_fecha = date(payload.periodo_anio, payload.periodo_mes, 1)

    try:
        datos_convenio = obtener_datos_convenio_contrato(db, contrato, en_fecha)
        parametros = obtener_parametros_cotizacion(
            db, en_fecha, datos_convenio.grupo_cotizacion, contrato.tipo_contrato
        )
        tramos_irpf = obtener_tramos_irpf(db, payload.periodo_anio)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    eventos = EventosMes(
        periodo_anio=payload.periodo_anio,
        periodo_mes=payload.periodo_mes,
        dias_naturales_periodo=payload.dias_naturales_periodo,
        dias_trabajados=payload.dias_trabajados,
        horas_extra=payload.horas_extra,
        horas_extra_nocturnas=payload.horas_extra_nocturnas,
        horas_nocturnas_ordinarias=payload.horas_nocturnas_ordinarias,
        dias_it=payload.dias_it,
        dias_vacaciones=payload.dias_vacaciones,
        dias_festivos_trabajados=payload.dias_festivos_trabajados,
        anticipos=payload.anticipos,
        embargo_mensual=payload.embargo_mensual,
        numero_medias_dietas=payload.numero_medias_dietas,
        numero_dietas_completas_cortas=payload.numero_dietas_completas_cortas,
        numero_dietas_completas_largas=payload.numero_dietas_completas_largas,
    )

    trabajador = contrato.trabajador
    edad = None
    if trabajador.fecha_nacimiento:
        edad = en_fecha.year - trabajador.fecha_nacimiento.year - (
            (en_fecha.month, en_fecha.day) < (trabajador.fecha_nacimiento.month, trabajador.fecha_nacimiento.day)
        )
    resultado = calcular_nomina(
        datos_convenio,
        eventos,
        parametros,
        tramos_irpf,
        hijos_menores_25=trabajador.hijos_menores_25,
        grado_discapacidad=trabajador.grado_discapacidad,
        edad=edad,
    )

    nomina.contrato_id = contrato.id
    nomina.periodo_anio = payload.periodo_anio
    nomina.periodo_mes = payload.periodo_mes
    nomina.tipo = payload.tipo
    nomina.dias_naturales_periodo = payload.dias_naturales_periodo
    nomina.dias_trabajados = payload.dias_trabajados or (payload.dias_naturales_periodo - payload.dias_it)
    nomina.horas_extra = payload.horas_extra
    nomina.horas_extra_nocturnas = payload.horas_extra_nocturnas
    nomina.horas_nocturnas_ordinarias = payload.horas_nocturnas_ordinarias
    nomina.dias_it = payload.dias_it
    nomina.dias_vacaciones = payload.dias_vacaciones
    nomina.dias_festivos_trabajados = payload.dias_festivos_trabajados
    nomina.anticipos = payload.anticipos
    nomina.embargo_mensual = payload.embargo_mensual
    nomina.numero_medias_dietas = payload.numero_medias_dietas
    nomina.numero_dietas_completas_cortas = payload.numero_dietas_completas_cortas
    nomina.numero_dietas_completas_largas = payload.numero_dietas_completas_largas
    nomina.total_devengado = resultado.total_devengado
    nomina.total_deducciones = resultado.total_deducciones
    nomina.liquido_a_percibir = resultado.liquido_a_percibir
    nomina.base_cotizacion_comun = resultado.base_cotizacion_comun
    nomina.base_sujeta_irpf = resultado.base_sujeta_irpf
    nomina.coste_empresa_total = resultado.coste_empresa_total
    nomina.total_dietas_exentas = resultado.total_dietas_exentas

    # Con los campos obligatorios ya rellenos, se puede insertar (si es nueva)
    # o simplemente asegurar que los cambios estén flush-eados (si ya
    # existía) para poder referenciar nomina.id al crear las líneas.
    db.add(nomina)
    db.flush()

    nomina.lineas.clear()
    for orden, linea in enumerate(resultado.lineas):
        db.add(
            NominaLinea(
                nomina_id=nomina.id,
                bloque=linea.bloque,
                concepto=linea.concepto,
                cantidad=linea.cantidad,
                base=linea.base,
                tipo_pct=linea.tipo_pct,
                importe=linea.importe,
                referencia_legal=linea.referencia_legal,
                orden=orden,
                cotiza=linea.cotiza,
            )
        )


@router.post("/generar", response_model=NominaOut, status_code=201)
def generar_nomina(payload: GenerarNominaRequest, db: Session = Depends(get_db)):
    nomina = Nomina()
    _calcular_y_poblar(nomina, payload, db)
    db.commit()
    db.refresh(nomina)
    return nomina


@router.get("", response_model=list[NominaOut])
def listar_nominas(contrato_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Nomina)
    if contrato_id is not None:
        query = query.filter(Nomina.contrato_id == contrato_id)
    return query.order_by(Nomina.periodo_anio.desc(), Nomina.periodo_mes.desc()).all()


@router.get("/{nomina_id}", response_model=NominaOut)
def obtener_nomina(nomina_id: int, db: Session = Depends(get_db)):
    nomina = db.get(Nomina, nomina_id)
    if not nomina:
        raise HTTPException(status_code=404, detail="Nómina no encontrada")
    return nomina


@router.put("/{nomina_id}", response_model=NominaOut)
def actualizar_nomina(nomina_id: int, payload: GenerarNominaRequest, db: Session = Depends(get_db)):
    """Recalcula por completo una nómina ya generada con nuevos datos de
    entrada, conservando su id (para poder corregirla sin duplicarla)."""
    nomina = db.get(Nomina, nomina_id)
    if not nomina:
        raise HTTPException(status_code=404, detail="Nómina no encontrada")

    _calcular_y_poblar(nomina, payload, db)
    db.commit()
    db.refresh(nomina)
    return nomina


@router.delete("/{nomina_id}", status_code=204)
def eliminar_nomina(nomina_id: int, db: Session = Depends(get_db)):
    nomina = db.get(Nomina, nomina_id)
    if not nomina:
        raise HTTPException(status_code=404, detail="Nómina no encontrada")
    db.delete(nomina)
    db.commit()


@router.get("/{nomina_id}/pdf")
def descargar_pdf_nomina(nomina_id: int, db: Session = Depends(get_db)):
    nomina = db.get(Nomina, nomina_id)
    if not nomina:
        raise HTTPException(status_code=404, detail="Nómina no encontrada")

    ruta_pdf = generar_pdf_nomina(nomina)
    nombre_archivo = f"nomina_{nomina.contrato.trabajador.apellidos}_{nomina.periodo_anio}_{nomina.periodo_mes:02d}.pdf"
    return FileResponse(ruta_pdf, media_type="application/pdf", filename=nombre_archivo)
