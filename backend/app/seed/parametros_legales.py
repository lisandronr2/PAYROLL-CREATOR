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

# Tipos generales de cotización (Orden anual de cotización a la SS — orientativo 2026)
PARAMETROS_GENERALES = [
    ("smi_mensual", Decimal("1184.00"), None, "RD del Salario Mínimo Interprofesional (verificar valor 2026)"),
    ("tope_max_cotizacion", Decimal("4909.50"), None, "Orden de cotización a la SS (tope máximo mensual, verificar)"),
    ("tipo_cc_empresa", Decimal("23.60"), None, "Art. 144 LGSS; Orden de cotización (contingencias comunes empresa)"),
    ("tipo_cc_trabajador", Decimal("4.70"), None, "Art. 144 LGSS; Orden de cotización (contingencias comunes trabajador)"),
    ("tipo_desempleo_indefinido_empresa", Decimal("5.50"), None, "Art. 227 LGSS (contrato indefinido, empresa)"),
    ("tipo_desempleo_indefinido_trabajador", Decimal("1.55"), None, "Art. 227 LGSS (contrato indefinido, trabajador)"),
    ("tipo_desempleo_temporal_empresa", Decimal("6.70"), None, "Art. 227 LGSS (contrato temporal, empresa)"),
    ("tipo_desempleo_temporal_trabajador", Decimal("1.60"), None, "Art. 227 LGSS (contrato temporal, trabajador)"),
    ("tipo_fp_empresa", Decimal("0.60"), None, "Orden de cotización a la SS (formación profesional, empresa)"),
    ("tipo_fp_trabajador", Decimal("0.10"), None, "Orden de cotización a la SS (formación profesional, trabajador)"),
    ("tipo_fogasa_empresa", Decimal("0.20"), None, "Art. 33 Estatuto de los Trabajadores (FOGASA)"),
    ("tipo_mei_empresa", Decimal("0.75"), None, "DA 21ª LGSS (Ley 21/2021); Orden PJC/297/2026 — MEI 2026: 0.90% total"),
    ("tipo_mei_trabajador", Decimal("0.15"), None, "DA 21ª LGSS (Ley 21/2021); Orden PJC/297/2026 — MEI 2026: 0.90% total"),
    ("recargo_hora_extra_pct", Decimal("75"), None, "Art. 35 ET (recargo mínimo 75%, o el pactado en convenio)"),
    ("recargo_hora_extra_nocturna_pct", Decimal("100"), None, "Convenio colectivo aplicable (orientativo)"),
    ("plus_nocturnidad_pct", Decimal("25"), None, "Art. 36 ET (recargo mínimo 25%, o el pactado en convenio)"),
]

# Tope mínimo de cotización por grupo de cotización (orientativo 2026, verificar Orden anual)
TOPES_MINIMOS_POR_GRUPO = [
    (1, Decimal("1929.00")),
    (2, Decimal("1929.00")),
    (3, Decimal("1679.40")),
    (4, Decimal("1466.40")),
    (5, Decimal("1466.40")),
    (6, Decimal("1466.40")),
    (7, Decimal("1466.40")),
    (8, Decimal("1466.40")),
    (9, Decimal("1466.40")),
    (10, Decimal("1466.40")),
    (11, Decimal("1466.40")),
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
CORRECCIONES = [
    ("tipo_mei_empresa", Decimal("0.58"), Decimal("0.75")),
    ("tipo_mei_trabajador", Decimal("0.12"), Decimal("0.15")),
]


def corregir_parametros_legales(db: Session) -> None:
    for clave, valor_incorrecto, valor_correcto in CORRECCIONES:
        parametro = (
            db.query(ParametroLegal)
            .filter(ParametroLegal.clave == clave, ParametroLegal.vigente_hasta.is_(None))
            .order_by(ParametroLegal.vigente_desde.desc())
            .first()
        )
        if parametro is not None and Decimal(parametro.valor) == valor_incorrecto:
            parametro.valor = valor_correcto
    db.commit()
