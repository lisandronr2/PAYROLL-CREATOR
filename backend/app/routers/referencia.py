"""
Endpoints de solo lectura para que cualquier usuario autenticado (no solo
admin) pueda consultar de un vistazo los parámetros que el motor aplica al
calcular una nómina: parámetros legales vigentes (SMI, topes de cotización,
recargos de horas extra/nocturnidad, tipos de cotización) y las dietas del
convenio elegido. No permite editar nada — para eso está el panel de admin.
"""
import calendar
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.engine.calculo import calcular_cotizacion, calcular_devengos, calcular_prorrata_pagas_extra
from app.engine.repositorio import obtener_datos_convenio_categoria, obtener_parametros_cotizacion
from app.engine.tipos import EventosMes
from app.models.convenio import CategoriaProfesional, ConvenioDieta
from app.models.empresa import Empresa
from app.models.parametro_legal import ParametroLegal
from app.models.parametro_negocio import ParametroNegocio
from app.schemas.parametro_legal import ParametroLegalOut
from app.schemas.parametro_negocio import ParametroNegocioOut
from app.schemas.referencia import ConvenioDietaOut, CosteCategoriaOut, CostePlantillaOut

router = APIRouter(prefix="/referencia", tags=["referencia"], dependencies=[Depends(get_current_usuario)])

HORAS_JORNADA_NORMAL = Decimal("8")


def _dias_laborables_mes(anio: int, mes: int, festivos_adicionales: int) -> tuple[int, int]:
    """Días naturales y días laborables (lunes-viernes, menos festivos que
    indique el usuario) de un mes — no hay calendario de festivos nacionales/
    autonómicos/locales cargado en la aplicación, así que hay que indicarlos
    a mano si el mes tiene alguno."""
    dias_naturales = calendar.monthrange(anio, mes)[1]
    dias_laborables = sum(
        1 for dia in range(1, dias_naturales + 1) if date(anio, mes, dia).weekday() < 5
    )
    dias_laborables = max(0, dias_laborables - festivos_adicionales)
    return dias_naturales, dias_laborables


@router.get("/parametros-legales", response_model=list[ParametroLegalOut])
def parametros_legales_vigentes(db: Session = Depends(get_db)):
    hoy = date.today()
    return (
        db.query(ParametroLegal)
        .filter(ParametroLegal.vigente_desde <= hoy)
        .filter((ParametroLegal.vigente_hasta.is_(None)) | (ParametroLegal.vigente_hasta >= hoy))
        .order_by(ParametroLegal.clave, ParametroLegal.grupo_cotizacion)
        .all()
    )


@router.get("/parametros-negocio", response_model=list[ParametroNegocioOut])
def parametros_negocio(db: Session = Depends(get_db)):
    return db.query(ParametroNegocio).order_by(ParametroNegocio.clave).all()


@router.get("/convenios/{convenio_id}/dietas", response_model=list[ConvenioDietaOut])
def dietas_convenio(convenio_id: int, db: Session = Depends(get_db)):
    hoy = date.today()
    return (
        db.query(ConvenioDieta)
        .filter(ConvenioDieta.convenio_id == convenio_id)
        .filter(ConvenioDieta.vigente_desde <= hoy)
        .filter((ConvenioDieta.vigente_hasta.is_(None)) | (ConvenioDieta.vigente_hasta >= hoy))
        .order_by(ConvenioDieta.vigente_desde.desc())
        .all()
    )


@router.get("/coste-categoria", response_model=CosteCategoriaOut)
def coste_categoria(
    empresa_id: int,
    categoria_id: int,
    anio: int,
    mes: int,
    festivos_adicionales: int = 0,
    db: Session = Depends(get_db),
):
    """
    Coste mensual y por hora de un empleado de una categoría de convenio,
    en una empresa concreta (el tipo AT/EP de cotización depende de la
    empresa), para un mes/año dado. El coste MENSUAL no cambia según el mes
    (el salario de convenio es fijo), pero el coste POR HORA sí, porque cada
    mes tiene un número distinto de días laborables.
    """
    if not (1 <= mes <= 12):
        raise HTTPException(status_code=422, detail="El mes debe estar entre 1 y 12")

    categoria = db.get(CategoriaProfesional, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if db.get(Empresa, empresa_id) is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    en_fecha = date(anio, mes, 1)
    try:
        convenio_datos = obtener_datos_convenio_categoria(db, categoria_id, empresa_id, en_fecha)
        parametros = obtener_parametros_cotizacion(db, en_fecha, categoria.grupo_cotizacion)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))

    dias_naturales_mes, dias_laborables_mes = _dias_laborables_mes(anio, mes, festivos_adicionales)

    eventos = EventosMes(
        periodo_anio=anio,
        periodo_mes=mes,
        dias_naturales_periodo=dias_naturales_mes,
        dias_trabajados=dias_naturales_mes,
    )
    _, suma_devengos_base, base_pagas_extra = calcular_devengos(convenio_datos, eventos)
    _, importe_prorrata_pagado, importe_prorrata_cotizable = calcular_prorrata_pagas_extra(
        convenio_datos, base_pagas_extra
    )
    total_devengado = suma_devengos_base + importe_prorrata_pagado
    base_cotizable = suma_devengos_base + importe_prorrata_cotizable
    _, _, _, cuota_empresa = calcular_cotizacion(parametros, base_cotizable, convenio_datos.tipo_at_ep_pct)

    coste_empresa_mensual = (total_devengado + cuota_empresa).quantize(Decimal("0.01"))
    horas_mes = Decimal(dias_laborables_mes) * HORAS_JORNADA_NORMAL
    coste_empresa_por_hora = (
        (coste_empresa_mensual / horas_mes).quantize(Decimal("0.01")) if horas_mes else Decimal("0")
    )

    return CosteCategoriaOut(
        anio=anio,
        mes=mes,
        dias_naturales_mes=dias_naturales_mes,
        dias_laborables_mes=dias_laborables_mes,
        horas_mes=horas_mes,
        convenio_nombre=convenio_datos.nombre_convenio,
        categoria_grupo=categoria.grupo,
        categoria_nombre=categoria.nombre,
        salario_base_mensual=suma_devengos_base.quantize(Decimal("0.01")),
        prorrata_pagas_extra_mensual=importe_prorrata_pagado.quantize(Decimal("0.01")),
        total_devengado_mensual=total_devengado.quantize(Decimal("0.01")),
        cuota_empresa_ss_mensual=cuota_empresa.quantize(Decimal("0.01")),
        coste_empresa_mensual=coste_empresa_mensual,
        coste_empresa_por_hora=coste_empresa_por_hora,
    )


@router.get("/coste-plantilla", response_model=CostePlantillaOut)
def coste_plantilla(
    empresa_id: int,
    categoria_id: int,
    anio: int,
    mes: int,
    numero_empleados: int,
    festivos_adicionales: int = 0,
    horas_extra_total: Decimal = Decimal("0"),
    combustible: Decimal = Decimal("0"),
    alojamiento: Decimal = Decimal("0"),
    dietas: Decimal = Decimal("0"),
    gastos_varios: Decimal = Decimal("0"),
    db: Session = Depends(get_db),
):
    """
    Coste real por empleado de una categoría, para un grupo de N empleados
    en un mes concreto: parte del coste laboral individual (salario +
    prorrata + horas extra repartidas entre la plantilla, más la cotización
    empresarial a la Seguridad Social sobre esa base) y le suma la parte
    proporcional de los gastos del grupo (combustible, alojamiento, dietas,
    gastos varios) repartidos entre el número de empleados. Estos gastos no
    cotizan a la Seguridad Social (son compensación de gastos, no salario),
    igual que las dietas en una nómina real.

    Las horas extra se reparten a partes iguales entre los N empleados y se
    valoran al precio de la hora real de este mes (coste laboral mensual /
    horas laborables reales del mes), con el recargo legal de hora extra —
    no con la fórmula legal exacta (salario anual/jornada anual), para
    mantener coherente el mismo "precio de la hora real" usado en todo el
    cálculo. Es una estimación de coste, no sustituye una nómina real.
    """
    if not (1 <= mes <= 12):
        raise HTTPException(status_code=422, detail="El mes debe estar entre 1 y 12")
    if numero_empleados < 1:
        raise HTTPException(status_code=422, detail="El número de empleados debe ser al menos 1")

    categoria = db.get(CategoriaProfesional, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if db.get(Empresa, empresa_id) is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    en_fecha = date(anio, mes, 1)
    try:
        convenio_datos = obtener_datos_convenio_categoria(db, categoria_id, empresa_id, en_fecha)
        parametros = obtener_parametros_cotizacion(db, en_fecha, categoria.grupo_cotizacion)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))

    dias_naturales_mes, dias_laborables_mes = _dias_laborables_mes(anio, mes, festivos_adicionales)
    horas_mes = Decimal(dias_laborables_mes) * HORAS_JORNADA_NORMAL

    eventos = EventosMes(
        periodo_anio=anio,
        periodo_mes=mes,
        dias_naturales_periodo=dias_naturales_mes,
        dias_trabajados=dias_naturales_mes,
    )
    _, suma_devengos_base, base_pagas_extra = calcular_devengos(convenio_datos, eventos)
    _, importe_prorrata_pagado, importe_prorrata_cotizable = calcular_prorrata_pagas_extra(
        convenio_datos, base_pagas_extra
    )
    total_devengado_sin_extra = suma_devengos_base + importe_prorrata_pagado
    base_cotizable_sin_extra = suma_devengos_base + importe_prorrata_cotizable

    coste_laboral_mensual_sin_ss = total_devengado_sin_extra
    precio_hora_real = (
        (coste_laboral_mensual_sin_ss / horas_mes).quantize(Decimal("0.01")) if horas_mes else Decimal("0")
    )

    horas_extra_individual = (horas_extra_total / numero_empleados).quantize(Decimal("0.01"))
    recargo = Decimal(1) + parametros.recargo_hora_extra_pct / Decimal(100)
    importe_horas_extra_individual = (horas_extra_individual * precio_hora_real * recargo).quantize(
        Decimal("0.01")
    )

    total_devengado_individual = total_devengado_sin_extra + importe_horas_extra_individual
    base_cotizable_individual = base_cotizable_sin_extra + importe_horas_extra_individual
    _, _, _, cuota_empresa_individual = calcular_cotizacion(
        parametros, base_cotizable_individual, convenio_datos.tipo_at_ep_pct
    )
    coste_laboral_individual = (total_devengado_individual + cuota_empresa_individual).quantize(Decimal("0.01"))

    gastos_reparto_total = (combustible + alojamiento + dietas + gastos_varios).quantize(Decimal("0.01"))
    gastos_reparto_individual = (gastos_reparto_total / numero_empleados).quantize(Decimal("0.01"))

    coste_real_individual = (coste_laboral_individual + gastos_reparto_individual).quantize(Decimal("0.01"))
    coste_total_plantilla = (coste_real_individual * numero_empleados).quantize(Decimal("0.01"))

    return CostePlantillaOut(
        anio=anio,
        mes=mes,
        dias_naturales_mes=dias_naturales_mes,
        dias_laborables_mes=dias_laborables_mes,
        horas_mes=horas_mes,
        convenio_nombre=convenio_datos.nombre_convenio,
        categoria_grupo=categoria.grupo,
        categoria_nombre=categoria.nombre,
        numero_empleados=numero_empleados,
        precio_hora_real=precio_hora_real,
        salario_base_mensual_individual=suma_devengos_base.quantize(Decimal("0.01")),
        prorrata_pagas_extra_individual=importe_prorrata_pagado.quantize(Decimal("0.01")),
        horas_extra_total=horas_extra_total,
        horas_extra_individual=horas_extra_individual,
        importe_horas_extra_individual=importe_horas_extra_individual,
        total_devengado_individual=total_devengado_individual.quantize(Decimal("0.01")),
        cuota_empresa_ss_individual=cuota_empresa_individual.quantize(Decimal("0.01")),
        coste_laboral_individual=coste_laboral_individual,
        gastos_reparto_total=gastos_reparto_total,
        gastos_reparto_individual=gastos_reparto_individual,
        coste_real_individual=coste_real_individual,
        coste_total_plantilla=coste_total_plantilla,
    )
