"""
Motor de cálculo de "Presupuesto por items": el presupuesto se construye a
partir de partidas de un catálogo de precios (mano de obra + material +
medios auxiliares por unidad de obra), en vez de personal por horas.

Cada partida del catálogo ya lleva su margen aplicado en el precio de
venta, así que aquí NO se vuelven a aplicar gastos generales ni margen
global (a diferencia de app/engine/presupuesto.py): solo se suma
precio_unitario × cantidad × (1 - descuento%) por línea, y al final se
aplica el IVA.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_importe_linea(precio_unitario: Decimal, cantidad: Decimal, descuento_pct: Decimal) -> Decimal:
    return _q(precio_unitario * cantidad * (1 - descuento_pct / Decimal(100)))


@dataclass
class ResultadoPresupuestoItems:
    subtotal: Decimal
    iva_importe: Decimal
    precio_total_cliente: Decimal


def calcular_totales_items(importes_lineas: list[Decimal], iva_pct: Decimal) -> ResultadoPresupuestoItems:
    subtotal = _q(sum(importes_lineas, Decimal("0")))
    iva_importe = _q(subtotal * iva_pct / Decimal(100))
    precio_total_cliente = _q(subtotal + iva_importe)
    return ResultadoPresupuestoItems(
        subtotal=subtotal,
        iva_importe=iva_importe,
        precio_total_cliente=precio_total_cliente,
    )
