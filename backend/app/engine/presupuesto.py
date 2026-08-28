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

El coste de personal ya NO se calcula a partir del salario de convenio: se
introduce un precio por hora (el que la empresa pacte según el cliente o
proyecto) y se aplica sobre jornadas normales de 8 horas por cada día de
dedicación. La categoría del convenio se conserva solo como referencia/
etiqueta en el presupuesto, no para calcular el coste.

Las dietas SÍ se siguen tomando del convenio elegido (media dieta, dieta
completa <7 días, dieta completa ≥7 días), como un coste directo por unidad
para todo el periodo del proyecto (no se prorratean).

⚠️ Es una estimación: no sustituye un estudio de costes real de la empresa.
El precio por hora, los gastos generales, el margen y el IVA son decisiones
de negocio del usuario, no datos legales — ver ParametroNegocio.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

# Horas de una jornada normal, usadas para convertir "días de dedicación" en
# horas facturables al precio/hora indicado.
HORAS_JORNADA_NORMAL = Decimal("8")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class LineaPersonalInput:
    precio_hora: Decimal
    cantidad_personas: int
    dias_dedicacion: Decimal
    numero_medias_dietas: int = 0
    numero_dietas_completas_cortas: int = 0
    numero_dietas_completas_largas: int = 0


@dataclass
class LineaPersonalResultado:
    coste_mano_obra_unitario: Decimal  # por una persona, para su dedicación al proyecto (sin dietas)
    coste_dietas_unitario: Decimal  # por una persona
    coste_unitario: Decimal  # mano_obra_unitario + dietas_unitario
    coste_mano_obra_total: Decimal  # coste_mano_obra_unitario * cantidad_personas
    coste_dietas_total: Decimal  # coste_dietas_unitario * cantidad_personas
    coste_total_linea: Decimal  # coste_mano_obra_total + coste_dietas_total


def calcular_linea_personal(
    entrada: LineaPersonalInput,
    media_dieta: Decimal,
    dieta_completa_corta: Decimal,
    dieta_completa_larga: Decimal,
) -> LineaPersonalResultado:
    # 1) Mano de obra: precio/hora pactado × 8 horas de jornada normal × días
    # de dedicación al proyecto. No interviene el convenio ni las cotizaciones.
    coste_mano_obra_unitario = _q(entrada.precio_hora * HORAS_JORNADA_NORMAL * entrada.dias_dedicacion)

    # 2) Dietas: sí vienen del convenio elegido, como coste directo por
    # unidad para todo el periodo (no se prorratean).
    coste_dietas_unitario = _q(
        entrada.numero_medias_dietas * media_dieta
        + entrada.numero_dietas_completas_cortas * dieta_completa_corta
        + entrada.numero_dietas_completas_largas * dieta_completa_larga
    )

    coste_unitario = _q(coste_mano_obra_unitario + coste_dietas_unitario)
    coste_mano_obra_total = _q(coste_mano_obra_unitario * entrada.cantidad_personas)
    coste_dietas_total = _q(coste_dietas_unitario * entrada.cantidad_personas)
    coste_total_linea = _q(coste_mano_obra_total + coste_dietas_total)

    return LineaPersonalResultado(
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
