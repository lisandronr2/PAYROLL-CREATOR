"""
Parámetros legales de partida para 2026.

⚠️ VALORES ORIENTATIVOS: los tipos de cotización, topes y SMI deben
verificarse cada año contra la Orden de Cotización a la Seguridad Social y
el Real Decreto del SMI vigentes antes de emitir nóminas reales. Editar
estos registros (tabla `parametros_legales`) o vía el futuro panel admin,
NO el código del motor.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.parametro_legal import ParametroLegal

VIGENTE_DESDE_2026 = date(2026, 1, 1)

# Tipos generales de cotización — verificados contra el RD 126/2026 (SMI) y
# la Orden PJC/297/2026, de 30 de marzo (cotización a la SS 2026, BOE
# 31/03/2026, con efectos desde el 01/01/2026).
PARAMETROS_GENERALES = [
    ("smi_mensual", Decimal("1221.00"), None, "RD 126/2026, de 18 de febrero (SMI 2026: 1.221€/mes en 14 pagas, 17.094€/año, 40,70€/día)"),
    ("tope_max_cotizacion", Decimal("5101.20"), None, "Orden PJC/297/2026 (tope máximo de cotización mensual 2026)"),
    ("tipo_cc_empresa", Decimal("23.60"), None, "Art. 144 LGSS; Orden PJC/297/2026 (contingencias comunes empresa)"),
    ("tipo_cc_trabajador", Decimal("4.70"), None, "Art. 144 LGSS; Orden PJC/297/2026 (contingencias comunes trabajador)"),
    ("tipo_desempleo_indefinido_empresa", Decimal("5.50"), None, "Art. 227 LGSS; Orden PJC/297/2026 (contrato indefinido, empresa — sin cambios sobre 2025)"),
    ("tipo_desempleo_indefinido_trabajador", Decimal("1.55"), None, "Art. 227 LGSS; Orden PJC/297/2026 (contrato indefinido, trabajador — sin cambios sobre 2025)"),
    ("tipo_desempleo_temporal_empresa", Decimal("6.70"), None, "Art. 227 LGSS; Orden PJC/297/2026 (contrato temporal, empresa — sin cambios sobre 2025)"),
    ("tipo_desempleo_temporal_trabajador", Decimal("1.60"), None, "Art. 227 LGSS; Orden PJC/297/2026 (contrato temporal, trabajador — sin cambios sobre 2025)"),
    ("tipo_fp_empresa", Decimal("0.60"), None, "Orden PJC/297/2026 (formación profesional, empresa — sin cambios sobre 2025)"),
    ("tipo_fp_trabajador", Decimal("0.10"), None, "Orden PJC/297/2026 (formación profesional, trabajador — sin cambios sobre 2025)"),
    ("tipo_fogasa_empresa", Decimal("0.20"), None, "Art. 33 Estatuto de los Trabajadores; Orden PJC/297/2026 (FOGASA — sin cambios sobre 2025)"),
    ("tipo_mei_empresa", Decimal("0.75"), None, "DA 21ª LGSS (Ley 21/2021); Orden PJC/297/2026 — MEI 2026: 0.90% total"),
    ("tipo_mei_trabajador", Decimal("0.15"), None, "DA 21ª LGSS (Ley 21/2021); Orden PJC/297/2026 — MEI 2026: 0.90% total"),
    ("recargo_hora_extra_pct", Decimal("75"), None, "Art. 35 ET (recargo mínimo 75%, o el pactado en convenio)"),
    ("recargo_hora_extra_nocturna_pct", Decimal("100"), None, "Convenio colectivo aplicable (orientativo)"),
    ("plus_nocturnidad_pct", Decimal("25"), None, "Art. 36 ET (recargo mínimo 25%, o el pactado en convenio)"),
]

# Base mínima de cotización por grupo — Orden PJC/297/2026 (grupos 1-7 en
# base mensual; grupos 8-11 se publican en base diaria — 47,48€/día× ~30 =
# 1.424,40€/mes equivalente, igual que los grupos 4-7 — y se guarda como
# equivalente mensual porque el motor solo maneja bases mensuales).
TOPES_MINIMOS_POR_GRUPO = [
    (1, Decimal("1989.30")),
    (2, Decimal("1649.70")),
    (3, Decimal("1435.20")),
    (4, Decimal("1424.40")),
    (5, Decimal("1424.40")),
    (6, Decimal("1424.40")),
    (7, Decimal("1424.40")),
    (8, Decimal("1424.40")),
    (9, Decimal("1424.40")),
    (10, Decimal("1424.40")),
    (11, Decimal("1424.40")),
]


def seed_parametros_legales(db: Session) -> None:
    if db.query(ParametroLegal).first() is not None:
        return

    for clave, valor, grupo, referencia in PARAMETROS_GENERALES:
        db.add(
            ParametroLegal(
                clave=clave,
                valor=valor,
                grupo_cotizacion=grupo,
                vigente_desde=VIGENTE_DESDE_2026,
                referencia_legal=referencia,
            )
        )

    for grupo, valor in TOPES_MINIMOS_POR_GRUPO:
        db.add(
            ParametroLegal(
                clave="tope_min_cotizacion",
                valor=valor,
                grupo_cotizacion=grupo,
                vigente_desde=VIGENTE_DESDE_2026,
                referencia_legal="Orden de cotización a la SS (base mínima por grupo, verificar)",
            )
        )

    db.commit()


# Correcciones a valores ya sembrados en despliegues anteriores (no basta con
# cambiar PARAMETROS_GENERALES arriba porque seed_parametros_legales() no
# vuelve a ejecutarse si ya hay filas). Idempotente: solo toca la fila si su
# valor actual coincide con el valor incorrecto conocido.
# Tupla: (clave, grupo_cotizacion|None, valor_incorrecto, valor_correcto)
CORRECCIONES = [
    ("tipo_mei_empresa", None, Decimal("0.58"), Decimal("0.75")),
    ("tipo_mei_trabajador", None, Decimal("0.12"), Decimal("0.15")),
    # SMI 2026 real (RD 126/2026): 1.221€/mes, no 1.184€ (SMI 2025).
    ("smi_mensual", None, Decimal("1184.00"), Decimal("1221.00")),
    # Tope máximo de cotización 2026 real (Orden PJC/297/2026): 5.101,20€.
    ("tope_max_cotizacion", None, Decimal("4909.50"), Decimal("5101.20")),
    # Bases mínimas de cotización por grupo 2026 reales (Orden PJC/297/2026).
    ("tope_min_cotizacion", 1, Decimal("1929.00"), Decimal("1989.30")),
    ("tope_min_cotizacion", 2, Decimal("1929.00"), Decimal("1649.70")),
    ("tope_min_cotizacion", 3, Decimal("1679.40"), Decimal("1435.20")),
    ("tope_min_cotizacion", 4, Decimal("1466.40"), Decimal("1424.40")),
    ("tope_min_cotizacion", 5, Decimal("1466.40"), Decimal("1424.40")),
    ("tope_min_cotizacion", 6, Decimal("1466.40"), Decimal("1424.40")),
    ("tope_min_cotizacion", 7, Decimal("1466.40"), Decimal("1424.40")),
    ("tope_min_cotizacion", 8, Decimal("1466.40"), Decimal("1424.40")),
    ("tope_min_cotizacion", 9, Decimal("1466.40"), Decimal("1424.40")),
    ("tope_min_cotizacion", 10, Decimal("1466.40"), Decimal("1424.40")),
    ("tope_min_cotizacion", 11, Decimal("1466.40"), Decimal("1424.40")),
]


def corregir_parametros_legales(db: Session) -> None:
    for clave, grupo, valor_incorrecto, valor_correcto in CORRECCIONES:
        query = db.query(ParametroLegal).filter(
            ParametroLegal.clave == clave, ParametroLegal.vigente_hasta.is_(None)
        )
        if grupo is not None:
            query = query.filter(ParametroLegal.grupo_cotizacion == grupo)
        parametro = query.order_by(ParametroLegal.vigente_desde.desc()).first()
        if parametro is not None and Decimal(parametro.valor) == valor_incorrecto:
            parametro.valor = valor_correcto
    db.commit()
