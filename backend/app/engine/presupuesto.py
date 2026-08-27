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

⚠️ Es una estimación: no sustituye un estudio de costes real de la empresa.
Los porcentajes de gastos generales, margen e IVA son decisiones de negocio
del usuario, no datos legales — ver ParametroNegocio.
"""
from dataclasses import dataclass, replace
from decimal import Decimal, ROUND_HALF_UP

from app.engine.calculo import calcular_nomina
from app.engine.tipos import DatosConvenioContrato, ParametrosCotizacion, EventosMes

DIAS_MES_REFERENCIA = Decimal("30")


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
    coste_salarial_prorrateado: Decimal
    coste_dietas: Decimal
    coste_unitario: Decimal  # por una persona, para toda su dedicación al proyecto
    coste_total_linea: Decimal  # coste_unitario * cantidad_personas


def calcular_linea_personal(
    datos_convenio: DatosConvenioContrato,
    parametros: ParametrosCotizacion,
    entrada: LineaPersonalInput,
    anio: int,
    mes: int,
) -> LineaPersonalResultado:
    # 1) Coste de un mes natural completo (30 días), sin dietas — la jornada,
    # la mejora voluntaria y si prorratea pagas extra ya vienen incluidas en
    # `datos_convenio`.
    datos_sin_dietas = replace(
        datos_convenio,
        media_dieta=Decimal("0"),
        dieta_completa_corta=Decimal("0"),
        dieta_completa_larga=Decimal("0"),
    )
    eventos_mes_completo = EventosMes(periodo_anio=anio, periodo_mes=mes, dias_naturales_periodo=30)
    resultado_mensual = calcular_nomina(datos_sin_dietas, eventos_mes_completo, parametros, [])
    coste_salarial_mensual_completo = resultado_mensual.coste_empresa_total

    # 2) Prorrateo por los días reales de dedicación al proyecto (base 30 días/mes).
    factor_dias = entrada.dias_dedicacion / DIAS_MES_REFERENCIA
    coste_salarial_prorrateado = _q(coste_salarial_mensual_completo * factor_dias)

    # 3) Dietas: coste directo por unidad para todo el periodo (no se prorratean).
    coste_dietas = _q(
        entrada.numero_medias_dietas * datos_convenio.media_dieta
        + entrada.numero_dietas_completas_cortas * datos_convenio.dieta_completa_corta
        + entrada.numero_dietas_completas_largas * datos_convenio.dieta_completa_larga
    )

    coste_unitario = coste_salarial_prorrateado + coste_dietas
    coste_total_linea = _q(coste_unitario * entrada.cantidad_personas)

    return LineaPersonalResultado(
        coste_salarial_mensual_completo=coste_salarial_mensual_completo,
        coste_salarial_prorrateado=coste_salarial_prorrateado,
        coste_dietas=coste_dietas,
        coste_unitario=coste_unitario,
        coste_total_linea=coste_total_linea,
    )


@dataclass
class ResultadoPresupuesto:
    coste_directo_personal: Decimal
    coste_directo_otros: Decimal
    coste_directo_total: Decimal
    gastos_generales_importe: Decimal
    coste_total: Decimal
    margen_importe: Decimal
    precio_venta: Decimal
    iva_importe: Decimal
    precio_total_cliente: Decimal


def calcular_totales_presupuesto(
    coste_directo_personal: Decimal,
    coste_directo_otros: Decimal,
    gastos_generales_pct: Decimal,
    margen_beneficio_pct: Decimal,
    iva_pct: Decimal,
) -> ResultadoPresupuesto:
    coste_directo_total = _q(coste_directo_personal + coste_directo_otros)
    gastos_generales_importe = _q(coste_directo_total * gastos_generales_pct / Decimal(100))
    coste_total = _q(coste_directo_total + gastos_generales_importe)
    margen_importe = _q(coste_total * margen_beneficio_pct / Decimal(100))
    precio_venta = _q(coste_total + margen_importe)
    iva_importe = _q(precio_venta * iva_pct / Decimal(100))
    precio_total_cliente = _q(precio_venta + iva_importe)

    return ResultadoPresupuesto(
        coste_directo_personal=_q(coste_directo_personal),
        coste_directo_otros=_q(coste_directo_otros),
        coste_directo_total=coste_directo_total,
        gastos_generales_importe=gastos_generales_importe,
        coste_total=coste_total,
        margen_importe=margen_importe,
        precio_venta=precio_venta,
        iva_importe=iva_importe,
        precio_total_cliente=precio_total_cliente,
    )
