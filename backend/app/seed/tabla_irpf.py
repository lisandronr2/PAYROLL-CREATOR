"""
Tabla de tramos IRPF 2026 (tarifa estatal + autonómica agregada, orientativa).

⚠️ Uso simplificado del procedimiento general de retención (arts. 80-87
Reglamento IRPF). Verificar tramos y mínimos personales/familiares vigentes
con la AEAT o una asesoría fiscal antes de usar en producción.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.tabla_irpf import TablaIRPF

VIGENTE_DESDE_2026 = date(2026, 1, 1)

TRAMOS_2026 = [
    (Decimal("0"), Decimal("12450"), Decimal("19")),
    (Decimal("12450"), Decimal("20200"), Decimal("24")),
    (Decimal("20200"), Decimal("35200"), Decimal("30")),
    (Decimal("35200"), Decimal("60000"), Decimal("37")),
    (Decimal("60000"), Decimal("300000"), Decimal("45")),
    (Decimal("300000"), None, Decimal("47")),
]


def seed_tabla_irpf(db: Session) -> None:
    if db.query(TablaIRPF).filter(TablaIRPF.anio == 2026).first() is not None:
        return

    for desde, hasta, tipo in TRAMOS_2026:
        db.add(
            TablaIRPF(
                anio=2026,
                base_desde_anual=desde,
                base_hasta_anual=hasta,
                tipo_aplicable_pct=tipo,
                vigente_desde=VIGENTE_DESDE_2026,
            )
        )
    db.commit()
