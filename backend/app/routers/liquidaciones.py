"""
Liquidación (finiquito) de un trabajador a partir de su contrato. Solo
calcula y devuelve el desglose: no guarda nada ni modifica el contrato ni la
fecha de baja del trabajador.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.engine.finiquito import (
    DIAS_NATURALES_VACACIONES_MINIMO,
    MOTIVOS,
    EntradaLiquidacion,
    calcular_liquidacion,
)
from app.engine.repositorio import (
    obtener_datos_convenio_contrato,
    obtener_parametros_cotizacion,
    obtener_tramos_irpf,
)
from app.models.contrato import Contrato
from app.schemas.liquidacion import (
    CalcularLiquidacionRequest,
    LiquidacionOut,
    LineaLiquidacionOut,
    SugerenciasLiquidacionOut,
)

router = APIRouter(prefix="/liquidaciones", tags=["liquidaciones"], dependencies=[Depends(get_current_usuario)])

PREAVISO_CESE_GENERICO_DIAS = 15
PREAVISO_DESPIDO_OBJETIVO_DIAS = 15  # art. 53.1.c ET
PREAVISO_TEMPORAL_DIAS = 15  # art. 49.1.c ET, contratos de más de un año


def _grupo_principal(grupo: str) -> int | None:
    try:
        return int(str(grupo).split(".")[0])
    except ValueError:
        return None


def _preaviso_sugerido(contrato: Contrato, motivo: str, fecha_ingreso: date, fecha_baja: date | None) -> tuple[int, str]:
    convenio = contrato.convenio
    if motivo == "dimision":
        es_tecnico = _grupo_principal(contrato.categoria.grupo) in (1, 2)
        if es_tecnico and convenio.preaviso_cese_dias_tecnicos is not None:
            return (
                convenio.preaviso_cese_dias_tecnicos,
                f"{convenio.preaviso_cese_dias_tecnicos} días: personal técnico y titulado según el convenio "
                "(grupos profesionales 1 y 2). Si la categoría no es técnica, cámbialo.",
            )
        if convenio.preaviso_cese_dias_resto is not None:
            return (
                convenio.preaviso_cese_dias_resto,
                f"{convenio.preaviso_cese_dias_resto} días naturales según el convenio para el resto del personal.",
            )
        return (
            PREAVISO_CESE_GENERICO_DIAS,
            f"{PREAVISO_CESE_GENERICO_DIAS} días: uso habitual; el convenio no lo tiene informado en la aplicación.",
        )
    if motivo == "despido_objetivo":
        return PREAVISO_DESPIDO_OBJETIVO_DIAS, "15 días de preaviso de la empresa (art. 53.1.c ET)."
    if motivo == "fin_contrato_temporal":
        if fecha_baja is not None and (fecha_baja - fecha_ingreso).days >= 365:
            return PREAVISO_TEMPORAL_DIAS, "15 días de preaviso: contrato temporal de más de un año (art. 49.1.c ET)."
        return 0, "Sin preaviso: solo es obligatorio en contratos temporales de más de un año (art. 49.1.c ET)."
    return 0, "Este motivo de baja no exige preaviso."


def _vacaciones_convenio(contrato: Contrato) -> tuple[int, int | None, str, str]:
    convenio = contrato.convenio
    naturales = convenio.vacaciones_dias_naturales or DIAS_NATURALES_VACACIONES_MINIMO
    laborables = convenio.vacaciones_dias_laborables
    if laborables:
        texto = f"{laborables} días laborables al año, nunca menos de {naturales} naturales (según el convenio)."
        return naturales, laborables, "laborables", texto
    return (
        naturales,
        None,
        "naturales",
        f"{naturales} días naturales al año (mínimo legal del art. 38 ET; el convenio no lo tiene informado).",
    )


def _obtener_contrato(db: Session, contrato_id: int) -> Contrato:
    contrato = db.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato


@router.get("/sugerencias", response_model=SugerenciasLiquidacionOut)
def sugerencias(contrato_id: int, motivo: str = "dimision", fecha_baja: date | None = None, db: Session = Depends(get_db)):
    if motivo not in MOTIVOS:
        raise HTTPException(status_code=422, detail="Motivo de baja no válido")
    contrato = _obtener_contrato(db, contrato_id)
    fecha_ingreso = contrato.fecha_antiguedad or contrato.fecha_inicio
    dias_preaviso, texto_preaviso = _preaviso_sugerido(contrato, motivo, fecha_ingreso, fecha_baja)
    naturales, laborables, unidad, texto_vacaciones = _vacaciones_convenio(contrato)
    return SugerenciasLiquidacionOut(
        fecha_ingreso=fecha_ingreso,
        tipo_contrato=contrato.tipo_contrato,
        categoria=f"{contrato.categoria.grupo} — {contrato.categoria.nombre}",
        convenio_nombre=contrato.convenio.nombre,
        dias_preaviso_exigidos=dias_preaviso,
        texto_preaviso=texto_preaviso,
        vacaciones_dias_naturales=naturales,
        vacaciones_dias_laborables=laborables,
        unidad_vacaciones_defecto=unidad,
        texto_vacaciones=texto_vacaciones,
    )


@router.post("/calcular", response_model=LiquidacionOut)
def calcular(payload: CalcularLiquidacionRequest, db: Session = Depends(get_db)):
    if payload.motivo not in MOTIVOS:
        raise HTTPException(status_code=422, detail="Motivo de baja no válido")

    contrato = _obtener_contrato(db, payload.contrato_id)
    trabajador = contrato.trabajador
    fecha_ingreso = payload.fecha_ingreso or contrato.fecha_antiguedad or contrato.fecha_inicio

    try:
        datos_convenio = obtener_datos_convenio_contrato(db, contrato, payload.fecha_baja)
        parametros = obtener_parametros_cotizacion(
            db, payload.fecha_baja, datos_convenio.grupo_cotizacion, contrato.tipo_contrato
        )
        tramos_irpf = obtener_tramos_irpf(db, payload.fecha_baja.year)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    edad = None
    if trabajador.fecha_nacimiento:
        nac = trabajador.fecha_nacimiento
        edad = payload.fecha_baja.year - nac.year - ((payload.fecha_baja.month, payload.fecha_baja.day) < (nac.month, nac.day))

    if payload.dias_preaviso_exigidos is not None:
        dias_preaviso_exigidos = payload.dias_preaviso_exigidos
    else:
        dias_preaviso_exigidos, _ = _preaviso_sugerido(contrato, payload.motivo, fecha_ingreso, payload.fecha_baja)
    naturales, laborables, _, _ = _vacaciones_convenio(contrato)

    entrada = EntradaLiquidacion(
        convenio=datos_convenio,
        parametros=parametros,
        tramos_irpf=tramos_irpf,
        fecha_ingreso=fecha_ingreso,
        fecha_baja=payload.fecha_baja,
        motivo=payload.motivo,
        dias_preaviso_exigidos=dias_preaviso_exigidos,
        dias_preaviso_trabajados=payload.dias_preaviso_trabajados,
        vacaciones_dias_naturales=naturales,
        vacaciones_dias_laborables=laborables,
        vacaciones_disfrutadas=payload.vacaciones_disfrutadas,
        unidad_vacaciones=payload.unidad_vacaciones,
        vacaciones_pendientes_anteriores=payload.vacaciones_pendientes_anteriores,
        otras_cantidades=payload.otras_cantidades,
        indemnizacion_pactada=payload.indemnizacion_pactada,
        descuentos=payload.descuentos,
        hijos_menores_25=trabajador.hijos_menores_25 or 0,
        grado_discapacidad=trabajador.grado_discapacidad or 0,
        edad=edad,
    )
    try:
        r = calcular_liquidacion(entrada)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return LiquidacionOut(
        trabajador_nombre=f"{trabajador.nombre} {trabajador.apellidos}",
        trabajador_nif=trabajador.nif,
        convenio_nombre=contrato.convenio.nombre,
        categoria=f"{contrato.categoria.grupo} — {contrato.categoria.nombre}",
        motivo=payload.motivo,
        motivo_texto=MOTIVOS[payload.motivo],
        fecha_ingreso=fecha_ingreso,
        fecha_baja=payload.fecha_baja,
        antiguedad_texto=r.antiguedad_texto,
        dias_preaviso_exigidos=dias_preaviso_exigidos,
        dias_preaviso_trabajados=payload.dias_preaviso_trabajados,
        vacaciones_dias_naturales=naturales,
        vacaciones_dias_laborables=laborables,
        salario_diario_indemnizacion=r.salario_diario_indemnizacion,
        salario_diario_preaviso=r.salario_diario_preaviso,
        lineas=[LineaLiquidacionOut(**l.__dict__) for l in r.lineas],
        total_ingresos=r.total_ingresos,
        indemnizacion_legal=r.indemnizacion_legal,
        indemnizacion_exenta=r.indemnizacion_exenta,
        base_cotizacion=r.base_cotizacion,
        base_irpf=r.base_irpf,
        cotizacion_trabajador=r.cotizacion_trabajador,
        tipo_irpf_pct=r.tipo_irpf_pct,
        retencion_irpf=r.retencion_irpf,
        total_descuentos=r.total_descuentos,
        total_deducciones=r.total_deducciones,
        liquido_a_percibir=r.liquido_a_percibir,
        cuota_empresa_ss=r.cuota_empresa_ss,
        coste_empresa_total=r.coste_empresa_total,
        avisos=r.avisos,
    )
