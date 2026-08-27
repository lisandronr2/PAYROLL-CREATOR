"""
Motor de cálculo de presupuestos de proyecto.

Metodología igual a la usada en licitaciones de obra en España:

    Coste directo (personal + materiales/otros)
        + Gastos Generales de estructura (%)
        = Coste total del proyecto
        + Margen de beneficio (%)
        = Precio de venta (sin IVA)
        + IVA (%)
        = Precio final al cliente

El coste de personal se apoya en el motor de nóminas ya existente
(`calcular_nomina`) para obtener el coste real por categoría de convenio
(salario + cotizaciones a cargo de la empresa + prorrata de pagas extra),
evitando duplicar esa lógica. Las dietas se calculan aparte, como un coste
directo por unidad para todo el periodo del proyecto (no se prorratean
mensualmente como el salario).

El coste mensual completo de un trabajador (salario + prorrata de pagas
extra + todas las cotizaciones a cargo de la empresa) se prorratea por
DÍAS LABORABLES (20 días/mes de referencia), no por días naturales (30):
un trabajador cobra el sueldo íntegro del mes trabajando solo ~20-22 días
efectivos (los findes no se trabajan pero sí se cobran), así que el coste
real por día de dedicación a un proyecto es más alto que si se repartiera
entre los 30 días naturales. Esto es una decisión de la empresa, no un dato
legal — ver docs/LEGAL_DISCLAIMER.md.

⚠️ Es una estimación: no sustituye un estudio de costes real de la empresa.
Los porcentajes de gastos generales, margen e IVA son decisiones de negocio
del usuario, no datos legales — ver ParametroNegocio.
"""
from dataclasses import dataclass, replace
from decimal import Decimal, ROUND_HALF_UP

from app.engine.calculo import calcular_nomina
from app.engine.tipos import DatosConvenioContrato, ParametrosCotizacion, EventosMes

# Días laborables de referencia al mes, usados para calcular el coste por
# día de dedicación a un proyecto (ver nota arriba). No confundir con los
# 30 días naturales que usa el motor de nóminas para el sueldo mensual.
DIAS_LABORABLES_MES_REFERENCIA = Decimal("20")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class LineaPersonalInput:
    cantidad_personas: int
    dias_dedicacion: Decimal
    numero_medias_dietas: int = 0
    numero_dietas_completas_cortas: int = 0
    numero_dietas_completas_largas: int = 0


@dataclass
class LineaPersonalResultado:
    coste_salarial_mensual_completo: Decimal
    coste_mano_obra_unitario: Decimal  # por una persona, para su dedicación al proyecto (sin dietas)
    coste_dietas_unitario: Decimal  # por una persona
    coste_unitario: Decimal  # mano_obra_unitario + dietas_unitario
    coste_mano_obra_total: Decimal  # coste_mano_obra_unitario * cantidad_personas
    coste_dietas_total: Decimal  # coste_dietas_unitario * cantidad_personas
    coste_total_linea: Decimal  # coste_mano_obra_total + coste_dietas_total


def calcular_linea_personal(
    datos_convenio: DatosConvenioContrato,
    parametros: ParametrosCotizacion,
    entrada: LineaPersonalInput,
    anio: int,
    mes: int,
) -> LineaPersonalResultado:
    # 1) Coste de un mes natural completo (30 días), sin dietas — la jornada,
    # la mejora voluntaria y si prorratea pagas extra ya vienen incluidas en
    # `datos_convenio`. Este coste YA incluye salario + prorrata de pagas
    # extra + todas las cotizaciones a cargo de la empresa.
    datos_sin_dietas = replace(
        datos_convenio,
        media_dieta=Decimal("0"),
        dieta_completa_corta=Decimal("0"),
        dieta_completa_larga=Decimal("0"),
    )
    eventos_mes_completo = EventosMes(periodo_anio=anio, periodo_mes=mes, dias_naturales_periodo=30)
    resultado_mensual = calcular_nomina(datos_sin_dietas, eventos_mes_completo, parametros, [])
    coste_salarial_mensual_completo = resultado_mensual.coste_empresa_total

    # 2) Prorrateo por los días laborables reales de dedicación al proyecto
    # (base 20 días laborables/mes, no 30 días naturales — ver cabecera).
    factor_dias = entrada.dias_dedicacion / DIAS_LABORABLES_MES_REFERENCIA
    coste_mano_obra_unitario = _q(coste_salarial_mensual_completo * factor_dias)

    # 3) Dietas: coste directo por unidad para todo el periodo (no se prorratean).
    coste_dietas_unitario = _q(
        entrada.numero_medias_dietas * datos_convenio.media_dieta
        + entrada.numero_dietas_completas_cortas * datos_convenio.dieta_completa_corta
        + entrada.numero_dietas_completas_largas * datos_convenio.dieta_completa_larga
    )

    coste_unitario = _q(coste_mano_obra_unitario + coste_dietas_unitario)
    coste_mano_obra_total = _q(coste_mano_obra_unitario * entrada.cantidad_personas)
    coste_dietas_total = _q(coste_dietas_unitario * entrada.cantidad_personas)
    coste_total_linea = _q(coste_mano_obra_total + coste_dietas_total)

    return LineaPersonalResultado(
        coste_salarial_mensual_completo=coste_salarial_mensual_completo,
        coste_mano_obra_unitario=coste_mano_obra_unitario,
        coste_dietas_unitario=coste_dietas_unitario,
        coste_unitario=coste_unitario,
        coste_mano_obra_total=coste_mano_obra_total,
        coste_dietas_total=coste_dietas_total,
        coste_total_linea=coste_total_linea,
    )


@dataclass
class ResultadoPresupuesto:
    coste_directo_mano_obra: Decimal
    coste_directo_dietas: Decimal
    coste_directo_materiales: Decimal
    coste_directo_total: Decimal
    gastos_generales_importe: Decimal
    coste_total: Decimal
    margen_importe: Decimal
    precio_venta: Decimal
    iva_importe: Decimal
    precio_total_cliente: Decimal


def calcular_totales_presupuesto(
    coste_directo_mano_obra: Decimal,
    coste_directo_dietas: Decimal,
    coste_directo_materiales: Decimal,
    gastos_generales_pct: Decimal,
    margen_beneficio_pct: Decimal,
    iva_pct: Decimal,
) -> ResultadoPresupuesto:
    coste_directo_total = _q(coste_directo_mano_obra + coste_directo_dietas + coste_directo_materiales)
    gastos_generales_importe = _q(coste_directo_total * gastos_generales_pct / Decimal(100))
    coste_total = _q(coste_directo_total + gastos_generales_importe)
    margen_importe = _q(coste_total * margen_beneficio_pct / Decimal(100))
    precio_venta = _q(coste_total + margen_importe)
    iva_importe = _q(precio_venta * iva_pct / Decimal(100))
    precio_total_cliente = _q(precio_venta + iva_importe)

    return ResultadoPresupuesto(
        coste_directo_mano_obra=_q(coste_directo_mano_obra),
        coste_directo_dietas=_q(coste_directo_dietas),
        coste_directo_materiales=_q(coste_directo_materiales),
        coste_directo_total=coste_directo_total,
        gastos_generales_importe=gastos_generales_importe,
        coste_total=coste_total,
        margen_importe=margen_importe,
        precio_venta=precio_venta,
        iva_importe=iva_importe,
        precio_total_cliente=precio_total_cliente,
    )
