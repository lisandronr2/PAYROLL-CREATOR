"""
Parámetros de NEGOCIO por defecto para presupuestos: margen de beneficio,
gastos generales de estructura e IVA. A diferencia de los parámetros
legales, estos no salen de ninguna ley — son valores de referencia del
sector (construcción/instalaciones) que el usuario debe revisar y ajustar
a los números reales de su empresa desde Admin → Parámetros de negocio.
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.parametro_negocio import ParametroNegocio

VALORES_DEFECTO = [
    (
        "margen_beneficio_pct_defecto",
        Decimal("6"),
        "Margen de beneficio sobre el coste total. Referencia orientativa: 'Beneficio Industrial' "
        "del 6% usado en licitaciones de obra pública — ajústalo a lo que necesite tu empresa.",
    ),
    (
        "gastos_generales_pct_defecto",
        Decimal("15"),
        "Gastos generales de estructura (alquiler, seguros, vehículos, administración, etc.) como "
        "% del coste directo. Referencia orientativa: 13-17% en obra pública — ajústalo a tus "
        "gastos fijos anuales reales entre tu facturación anual.",
    ),
    (
        "iva_pct_defecto",
        Decimal("21"),
        "IVA general aplicado al precio de venta. Usa 10% si el proyecto es una reforma de "
        "vivienda que cumpla los requisitos del tipo reducido.",
    ),
]


def seed_parametros_negocio(db: Session) -> None:
    if db.query(ParametroNegocio).first() is not None:
        return
    for clave, valor, descripcion in VALORES_DEFECTO:
        db.add(ParametroNegocio(clave=clave, valor=valor, descripcion=descripcion))
    db.commit()
