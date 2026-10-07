"""
Liquidación (finiquito) de un trabajador a partir de su contrato.

- POST /calcular: calcula y devuelve el desglose sin guardar nada.
- POST / y PUT /{id}: calculan y guardan (o recalculan al editar) la
  liquidación, con sus datos de entrada y el resultado tal como se calculó.
- GET, DELETE y /pdf: consultar, borrar e imprimir las ya guardadas.

Ninguna de estas operaciones modifica el contrato ni da de baja al trabajador.
"""
import json
from dataclasses import dataclass
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.engine.finiquito import (
    DIAS_NATURALES_VACACIONES_MINIMO,
    MOTIVOS,
    EntradaLiquidacion,
    ResultadoLiquidacion,
    calcular_liquidacion,
)
from app.engine.repositorio import (
    obtener_datos_convenio_contrato,
    obtener_parametros_cotizacion,
    obtener_tramos_irpf,
)
from app.models.contrato import Contrato
from app.models.liquidacion import Liquidacion, LiquidacionLinea
from app.models.trabajador import Trabajador
from app.pdf.generador_liquidacion import generar_pdf_liquidacion
from app.schemas.liquidacion import (
    CalcularLiquidacionRequest,
    LiquidacionGuardadaOut,
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


def _obtener_liquidacion(db: Session, liquidacion_id: int) -> Liquidacion:
    liquidacion = db.get(Liquidacion, liquidacion_id)
    if not liquidacion:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    return liquidacion


@dataclass
class _Calculo:
    contrato: Contrato
    trabajador: Trabajador
    fecha_ingreso: date
    dias_preaviso_exigidos: int
    vacaciones_dias_naturales: int
    vacaciones_dias_laborables: int | None
    resultado: ResultadoLiquidacion


def _calcular(payload: CalcularLiquidacionRequest, db: Session) -> _Calculo:
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
        resultado = calcular_liquidacion(entrada)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return _Calculo(contrato, trabajador, fecha_ingreso, dias_preaviso_exigidos, naturales, laborables, resultado)


def _salida(payload: CalcularLiquidacionRequest, c: _Calculo) -> LiquidacionOut:
    r = c.resultado
    return LiquidacionOut(
        trabajador_nombre=f"{c.trabajador.nombre} {c.trabajador.apellidos}",
        trabajador_nif=c.trabajador.nif,
        convenio_nombre=c.contrato.convenio.nombre,
        categoria=f"{c.contrato.categoria.grupo} — {c.contrato.categoria.nombre}",
        motivo=payload.motivo,
        motivo_texto=MOTIVOS[payload.motivo],
        fecha_ingreso=c.fecha_ingreso,
        fecha_baja=payload.fecha_baja,
        antiguedad_texto=r.antiguedad_texto,
        dias_preaviso_exigidos=c.dias_preaviso_exigidos,
        dias_preaviso_trabajados=payload.dias_preaviso_trabajados,
        vacaciones_dias_naturales=c.vacaciones_dias_naturales,
        vacaciones_dias_laborables=c.vacaciones_dias_laborables,
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


def _poblar(liquidacion: Liquidacion, payload: CalcularLiquidacionRequest, c: _Calculo) -> None:
    """Copia datos de entrada y resultado a la liquidación (nueva o existente)."""
    r = c.resultado
    liquidacion.contrato_id = c.contrato.id
    liquidacion.trabajador_id = c.trabajador.id
    liquidacion.trabajador_nombre = f"{c.trabajador.nombre} {c.trabajador.apellidos}"
    liquidacion.trabajador_nif = c.trabajador.nif
    liquidacion.convenio_nombre = c.contrato.convenio.nombre
    liquidacion.categoria = f"{c.contrato.categoria.grupo} — {c.contrato.categoria.nombre}"

    liquidacion.motivo = payload.motivo
    liquidacion.motivo_texto = MOTIVOS[payload.motivo]
    liquidacion.fecha_ingreso = c.fecha_ingreso
    liquidacion.fecha_baja = payload.fecha_baja
    liquidacion.dias_preaviso_exigidos = c.dias_preaviso_exigidos
    liquidacion.dias_preaviso_trabajados = payload.dias_preaviso_trabajados
    liquidacion.vacaciones_disfrutadas = payload.vacaciones_disfrutadas
    liquidacion.unidad_vacaciones = payload.unidad_vacaciones
    liquidacion.vacaciones_pendientes_anteriores = payload.vacaciones_pendientes_anteriores
    liquidacion.otras_cantidades = payload.otras_cantidades
    liquidacion.indemnizacion_pactada = payload.indemnizacion_pactada
    liquidacion.descuentos = payload.descuentos
    liquidacion.notas = (payload.notas or "").strip() or None
    liquidacion.vacaciones_dias_naturales = c.vacaciones_dias_naturales
    liquidacion.vacaciones_dias_laborables = c.vacaciones_dias_laborables

    liquidacion.antiguedad_texto = r.antiguedad_texto
    liquidacion.salario_diario_indemnizacion = r.salario_diario_indemnizacion
    liquidacion.salario_diario_preaviso = r.salario_diario_preaviso
    liquidacion.total_ingresos = r.total_ingresos
    liquidacion.indemnizacion_legal = r.indemnizacion_legal
    liquidacion.indemnizacion_exenta = r.indemnizacion_exenta
    liquidacion.base_cotizacion = r.base_cotizacion
    liquidacion.base_irpf = r.base_irpf
    liquidacion.cotizacion_trabajador = r.cotizacion_trabajador
    liquidacion.tipo_irpf_pct = r.tipo_irpf_pct
    liquidacion.retencion_irpf = r.retencion_irpf
    liquidacion.total_descuentos = r.total_descuentos
    liquidacion.total_deducciones = r.total_deducciones
    liquidacion.liquido_a_percibir = r.liquido_a_percibir
    liquidacion.cuota_empresa_ss = r.cuota_empresa_ss
    liquidacion.coste_empresa_total = r.coste_empresa_total
    liquidacion.avisos_json = json.dumps(r.avisos, ensure_ascii=False)

    liquidacion.lineas.clear()
    for orden, linea in enumerate(r.lineas):
        liquidacion.lineas.append(
            LiquidacionLinea(
                orden=orden,
                bloque=linea.bloque,
                concepto=linea.concepto,
                importe=linea.importe,
                detalle=linea.detalle,
                referencia_legal=linea.referencia_legal,
                cotiza=linea.cotiza,
                tributa=linea.tributa,
            )
        )


# Las rutas fijas (/sugerencias, /calcular) van antes que /{liquidacion_id}.

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
    return _salida(payload, _calcular(payload, db))


@router.post("", response_model=LiquidacionGuardadaOut, status_code=201)
def crear_liquidacion(payload: CalcularLiquidacionRequest, db: Session = Depends(get_db)):
    calculo = _calcular(payload, db)
    liquidacion = Liquidacion()
    _poblar(liquidacion, payload, calculo)
    db.add(liquidacion)
    db.commit()
    db.refresh(liquidacion)
    return liquidacion


@router.get("", response_model=list[LiquidacionGuardadaOut])
def listar_liquidaciones(db: Session = Depends(get_db)):
    return db.query(Liquidacion).order_by(Liquidacion.creado_en.desc(), Liquidacion.id.desc()).all()


@router.get("/{liquidacion_id}", response_model=LiquidacionGuardadaOut)
def obtener_liquidacion(liquidacion_id: int, db: Session = Depends(get_db)):
    return _obtener_liquidacion(db, liquidacion_id)


@router.put("/{liquidacion_id}", response_model=LiquidacionGuardadaOut)
def actualizar_liquidacion(liquidacion_id: int, payload: CalcularLiquidacionRequest, db: Session = Depends(get_db)):
    liquidacion = _obtener_liquidacion(db, liquidacion_id)
    calculo = _calcular(payload, db)
    _poblar(liquidacion, payload, calculo)
    db.commit()
    db.refresh(liquidacion)
    return liquidacion


@router.delete("/{liquidacion_id}", status_code=204)
def eliminar_liquidacion(liquidacion_id: int, db: Session = Depends(get_db)):
    liquidacion = _obtener_liquidacion(db, liquidacion_id)
    db.delete(liquidacion)
    db.commit()


@router.get("/{liquidacion_id}/pdf")
def pdf_liquidacion(liquidacion_id: int, tipo: str = "trabajador", db: Session = Depends(get_db)):
    liquidacion = _obtener_liquidacion(db, liquidacion_id)
    if tipo not in ("trabajador", "interno"):
        raise HTTPException(status_code=422, detail="El parámetro 'tipo' debe ser 'trabajador' o 'interno'")
    ruta_pdf = generar_pdf_liquidacion(liquidacion, tipo=tipo)
    return FileResponse(
        ruta_pdf, media_type="application/pdf", filename=f"liquidacion_{liquidacion.id}_{tipo}.pdf"
    )
