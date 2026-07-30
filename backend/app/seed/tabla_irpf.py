"""
Tabla de tramos IRPF 2026 (tarifa estatal + autonómica de la Comunidad de
Madrid agregadas), calculada combinando:

- Escala estatal (art. 63.1 LIRPF 2026): 0-12.450€ 9,5% · 12.450-20.200€ 12%
  · 20.200-35.200€ 15% · 35.200-60.000€ 18,5% · 60.000-300.000€ 22,5% ·
  >300.000€ 24,5%.
- Escala autonómica Comunidad de Madrid 2026 (deflactada, Ley 5/2024):
  0-13.362€ 8,5% · 13.362-19.005€ 10,7% · 19.005-35.426€ 12,8% ·
  35.426-57.320€ 17,4% · >57.320€ 20,5%.

Al no coincidir los saltos de tramo de ambas escalas, la tarifa combinada
tiene más tramos que cada una por separado (se suman los tipos vigentes en
cada intervalo resultante de cruzar los dos escalones).

⚠️ Uso simplificado del procedimiento general de retención (arts. 80-87
Reglamento IRPF): esta tabla es solo la tarifa por tramos; el motor aplica
además el mínimo personal/familiar y la reducción por rentas bajas del
trabajo (ver app/engine/calculo.py). Solo aplicable a personas con
residencia fiscal en la Comunidad de Madrid — verificar con la AEAT o una
asesoría fiscal antes de usar en producción, y actualizar si otra comunidad
autónoma aplica.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.tabla_irpf import TablaIRPF

VIGENTE_DESDE_2026 = date(2026, 1, 1)

TRAMOS_2026 = [
    (Decimal("0"), Decimal("12450"), Decimal("18.0")),
    (Decimal("12450"), Decimal("13362"), Decimal("20.5")),
    (Decimal("13362"), Decimal("19005"), Decimal("22.7")),
    (Decimal("19005"), Decimal("20200"), Decimal("24.8")),
    (Decimal("20200"), Decimal("35200"), Decimal("27.8")),
    (Decimal("35200"), Decimal("35426"), Decimal("31.3")),
    (Decimal("35426"), Decimal("57320"), Decimal("35.9")),
    (Decimal("57320"), Decimal("60000"), Decimal("39.0")),
    (Decimal("60000"), Decimal("300000"), Decimal("43.0")),
    (Decimal("300000"), None, Decimal("45.0")),
]

# Tabla anterior (2026, simplificada a 6 tramos genéricos — no reflejaba la
# escala autonómica real de Madrid). Se usa solo para detectar de forma
# idempotente si una base ya sembrada tiene estos valores desactualizados y
# sustituirlos, sin tocar tablas que un admin ya haya editado a mano.
TRAMOS_2026_ANTIGUOS = [
    (Decimal("0"), Decimal("12450"), Decimal("19")),
    (Decimal("12450"), Decimal("20200"), Decimal("24")),
    (Decimal("20200"), Decimal("35200"), Decimal("30")),
    (Decimal("35200"), Decimal("60000"), Decimal("37")),
    (Decimal("60000"), Decimal("300000"), Decimal("45")),
    (Decimal("300000"), None, Decimal("47")),
]


def _insertar_tramos_2026(db: Session) -> None:
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


def seed_tabla_irpf(db: Session) -> None:
    if db.query(TablaIRPF).filter(TablaIRPF.anio == 2026).first() is not None:
        return
    _insertar_tramos_2026(db)
    db.commit()


def corregir_tabla_irpf(db: Session) -> None:
    """
    Sustituye la tabla 2026 antigua (6 tramos genéricos, sin la escala
    autonómica real de Madrid) por la combinada correcta (10 tramos),
    únicamente si lo sembrado coincide exactamente con la tabla antigua
    conocida — así no se pisa una tabla que un admin ya haya personalizado.
    """
    filas = (
        db.query(TablaIRPF)
        .filter(TablaIRPF.anio == 2026)
        .order_by(TablaIRPF.base_desde_anual)
        .all()
    )
    if len(filas) != len(TRAMOS_2026_ANTIGUOS):
        return

    for fila, (desde, hasta, tipo) in zip(filas, TRAMOS_2026_ANTIGUOS):
        if Decimal(fila.base_desde_anual) != desde:
            return
        if hasta is None:
            if fila.base_hasta_anual is not None:
                return
        elif fila.base_hasta_anual is None or Decimal(fila.base_hasta_anual) != hasta:
            return
        if Decimal(fila.tipo_aplicable_pct) != tipo:
            return

    for fila in filas:
        db.delete(fila)
    db.flush()
    _insertar_tramos_2026(db)
    db.commit()
