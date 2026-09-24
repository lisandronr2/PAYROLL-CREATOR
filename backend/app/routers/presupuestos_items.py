from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.engine.presupuesto_items import calcular_importe_linea, calcular_totales_items
from app.models.parametro_negocio import ParametroNegocio
from app.models.partida_catalogo import PartidaCatalogo
from app.models.presupuesto_items import PresupuestoItems, PresupuestoItemsLinea
from app.pdf.generador_presupuesto_items import generar_pdf_presupuesto_items
from app.schemas.presupuesto_items import PresupuestoItemsCreate, PresupuestoItemsOut

router = APIRouter(
    prefix="/presupuestos-items", tags=["presupuestos-items"], dependencies=[Depends(get_current_usuario)]
)


def _valor_negocio(db: Session, clave: str) -> Decimal:
    parametro = db.query(ParametroNegocio).filter(ParametroNegocio.clave == clave).first()
    if parametro is None:
        raise HTTPException(status_code=500, detail=f"Parámetro de negocio no configurado: {clave}")
    return Decimal(parametro.valor)


def _calcular_y_poblar(presupuesto: PresupuestoItems, payload: PresupuestoItemsCreate, db: Session) -> None:
    iva_pct = payload.iva_pct if payload.iva_pct is not None else _valor_negocio(db, "iva_pct_defecto")

    importes = []
    lineas_calculadas = []
    for linea_in in payload.lineas:
        partida = db.get(PartidaCatalogo, linea_in.partida_id)
        if partida is None:
            raise HTTPException(status_code=404, detail=f"Partida {linea_in.partida_id} no encontrada")
        importe = calcular_importe_linea(partida.precio_venta, linea_in.cantidad, linea_in.descuento_pct)
        importes.append(importe)
        lineas_calculadas.append((linea_in, partida, importe))

    totales = calcular_totales_items(importes, iva_pct)

    presupuesto.empresa_id = payload.empresa_id
    presupuesto.nombre = payload.nombre
    presupuesto.cliente_nombre = payload.cliente_nombre
    presupuesto.cliente_nif = payload.cliente_nif
    presupuesto.fecha = payload.fecha
    presupuesto.notas = payload.notas
    presupuesto.iva_pct = iva_pct
    presupuesto.subtotal = totales.subtotal
    presupuesto.iva_importe = totales.iva_importe
    presupuesto.precio_total_cliente = totales.precio_total_cliente

    db.add(presupuesto)
    db.flush()

    presupuesto.lineas.clear()
    for linea_in, partida, importe in lineas_calculadas:
        db.add(
            PresupuestoItemsLinea(
                presupuesto_id=presupuesto.id,
                partida_id=partida.id,
                familia=partida.familia,
                nombre=partida.nombre,
                unidad=partida.unidad,
                coste_directo_unitario=partida.coste_directo,
                margen_pct=partida.margen_pct,
                precio_unitario=partida.precio_venta,
                cantidad=linea_in.cantidad,
                descuento_pct=linea_in.descuento_pct,
                importe=importe,
            )
        )


@router.post("", response_model=PresupuestoItemsOut, status_code=201)
def crear_presupuesto_items(payload: PresupuestoItemsCreate, db: Session = Depends(get_db)):
    presupuesto = PresupuestoItems()
    _calcular_y_poblar(presupuesto, payload, db)
    db.commit()
    db.refresh(presupuesto)
    return presupuesto


@router.get("", response_model=list[PresupuestoItemsOut])
def listar_presupuestos_items(db: Session = Depends(get_db)):
    return db.query(PresupuestoItems).order_by(PresupuestoItems.creado_en.desc()).all()


@router.get("/{presupuesto_id}", response_model=PresupuestoItemsOut)
def obtener_presupuesto_items(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.get(PresupuestoItems, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return presupuesto


@router.put("/{presupuesto_id}", response_model=PresupuestoItemsOut)
def actualizar_presupuesto_items(presupuesto_id: int, payload: PresupuestoItemsCreate, db: Session = Depends(get_db)):
    presupuesto = db.get(PresupuestoItems, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    _calcular_y_poblar(presupuesto, payload, db)
    db.commit()
    db.refresh(presupuesto)
    return presupuesto


@router.delete("/{presupuesto_id}", status_code=204)
def eliminar_presupuesto_items(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.get(PresupuestoItems, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    db.delete(presupuesto)
    db.commit()


@router.get("/{presupuesto_id}/pdf")
def descargar_pdf_presupuesto_items(presupuesto_id: int, tipo: str = "cliente", db: Session = Depends(get_db)):
    presupuesto = db.get(PresupuestoItems, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if tipo not in ("cliente", "interno"):
        raise HTTPException(status_code=422, detail="El parámetro 'tipo' debe ser 'cliente' o 'interno'")

    ruta_pdf = generar_pdf_presupuesto_items(presupuesto, tipo=tipo)
    nombre_archivo = f"presupuesto_items_{presupuesto.id}_{tipo}.pdf"
    return FileResponse(ruta_pdf, media_type="application/pdf", filename=nombre_archivo)
