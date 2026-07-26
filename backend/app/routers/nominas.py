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


@router.post("/generar", response_model=NominaOut, status_code=201)
def generar_nomina(payload: GenerarNominaRequest, db: Session = Depends(get_db)):
    contrato = db.get(Contrato, payload.contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    en_fecha = date(payload.periodo_anio, payload.periodo_mes, 1)

    try:
        datos_convenio = obtener_datos_convenio_contrato(db, contrato, en_fecha)
        parametros = obtener_parametros_cotizacion(db, en_fecha, datos_convenio.grupo_cotizacion)
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
    )

    trabajador = contrato.trabajador
    resultado = calcular_nomina(
        datos_convenio,
        eventos,
        parametros,
        tramos_irpf,
        hijos_menores_25=trabajador.hijos_menores_25,
        grado_discapacidad=trabajador.grado_discapacidad,
    )

    nomina = Nomina(
        contrato_id=contrato.id,
        periodo_anio=payload.periodo_anio,
        periodo_mes=payload.periodo_mes,
        tipo=payload.tipo,
        dias_naturales_periodo=payload.dias_naturales_periodo,
        dias_trabajados=payload.dias_trabajados or (payload.dias_naturales_periodo - payload.dias_it),
        horas_extra=payload.horas_extra,
        dias_it=payload.dias_it,
        dias_vacaciones=payload.dias_vacaciones,
        total_devengado=resultado.total_devengado,
        total_deducciones=resultado.total_deducciones,
        liquido_a_percibir=resultado.liquido_a_percibir,
        base_cotizacion_comun=resultado.base_cotizacion_comun,
        base_sujeta_irpf=resultado.base_sujeta_irpf,
        coste_empresa_total=resultado.coste_empresa_total,
    )
    db.add(nomina)
    db.flush()

    for orden, linea in enumerate(resultado.lineas):
        db.add(
            NominaLinea(
                nomina_id=nomina.id,
                bloque=linea.bloque,
                concepto=linea.concepto,
                base=linea.base,
                tipo_pct=linea.tipo_pct,
                importe=linea.importe,
                referencia_legal=linea.referencia_legal,
                orden=orden,
            )
        )

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


@router.get("/{nomina_id}/pdf")
def descargar_pdf_nomina(nomina_id: int, db: Session = Depends(get_db)):
    nomina = db.get(Nomina, nomina_id)
    if not nomina:
        raise HTTPException(status_code=404, detail="Nómina no encontrada")

    ruta_pdf = generar_pdf_nomina(nomina)
    nombre_archivo = f"nomina_{nomina.contrato.trabajador.apellidos}_{nomina.periodo_anio}_{nomina.periodo_mes:02d}.pdf"
    return FileResponse(ruta_pdf, media_type="application/pdf", filename=nombre_archivo)
