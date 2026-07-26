"""
Cálculo de finiquito (liquidación por fin de contrato).

Componentes (simplificado, ver docs/LEGAL_DISCLAIMER.md):
  - Parte proporcional de pagas extraordinarias no devengadas en efectivo.
  - Vacaciones generadas y no disfrutadas (art. 38 ET).
  - Salario de los días trabajados del último mes (vía calcular_nomina).
  - Indemnización por fin de contrato, si procede según tipo de contrato
    (no incluida por defecto: requiere criterio jurídico caso a caso).
"""
from decimal import Decimal, ROUND_HALF_UP

from app.engine.tipos import DatosConvenioContrato, LineaCalculo

TWO = Decimal("0.01")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(TWO, rounding=ROUND_HALF_UP)


def calcular_partes_proporcionales(
    convenio: DatosConvenioContrato,
    suma_devengos_base_mensual: Decimal,
    dias_vacaciones_pendientes: int,
    dias_generados_desde_ultima_paga_extra: int,
) -> list[LineaCalculo]:
    lineas: list[LineaCalculo] = []

    if dias_vacaciones_pendientes:
        salario_dia = _q(suma_devengos_base_mensual / Decimal(30))
        importe = _q(salario_dia * dias_vacaciones_pendientes)
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"Vacaciones no disfrutadas ({dias_vacaciones_pendientes} días)",
                base=salario_dia,
                importe=importe,
                referencia_legal="Art. 38 Estatuto de los Trabajadores",
            )
        )

    if convenio.numero_pagas > 12 and not convenio.pagas_extra_prorrateadas:
        pagas_extra_anuales = convenio.numero_pagas - 12
        importe_dia = _q(
            suma_devengos_base_mensual * pagas_extra_anuales / Decimal(12) / Decimal(30)
        )
        importe = _q(importe_dia * dias_generados_desde_ultima_paga_extra)
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=(
                    "Parte proporcional pagas extraordinarias "
                    f"({dias_generados_desde_ultima_paga_extra} días)"
                ),
                importe=importe,
                referencia_legal="Art. 31 Estatuto de los Trabajadores",
            )
        )

    return lineas
