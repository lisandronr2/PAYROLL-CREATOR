"""
Convenios de ejemplo.

- Metal Madrid: datos REALES tomados de la revisión salarial 2026 publicada
  en el BOCM núm. 59 (11/03/2026) — Convenio Colectivo del Sector de
  Industria, Servicios e Instalaciones del Metal de Madrid.
- Construcción (VIII Convenio General del Sector): el convenio general
  estatal NO fija tablas salariales (se remiten a los convenios
  provinciales). Se incluye la estructura de grupos profesionales del
  convenio general con salarios de EJEMPLO — deben sustituirse por la
  tabla salarial del convenio provincial correspondiente.
- Comercio Madrid: convenio de EJEMPLO con valores orientativos, a
  verificar contra el texto y tablas oficiales vigentes.

⚠️ Ver docs/LEGAL_DISCLAIMER.md.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.convenio import Convenio, CategoriaProfesional, ConvenioTablaSalarial

VIGENTE_DESDE_2026 = date(2026, 1, 1)


def seed_convenios(db: Session) -> None:
    if db.query(Convenio).first() is not None:
        return

    # ---- 1) Metal Madrid (datos reales BOCM 11/03/2026) ----
    metal = Convenio(
        nombre="Industria, Servicios e Instalaciones del Metal de Madrid",
        ambito="provincial",
        provincia="Madrid",
        codigo_convenio="28003715011982",
        fuente="BOCM núm. 59, 11/03/2026 (corrección de errores; tablas salariales 2026)",
        numero_pagas=14,
        jornada_anual_horas=Decimal("1750"),
        notas="Tablas salariales reales 2026. Quinquenios (art. 41). Verificar vigencia anual.",
    )
    db.add(metal)
    db.flush()

    grupos_metal = [
        ("1", "Licenciada/o - Grado", 1, "35378.96", "2527.07", "1130.84"),
        ("2", "Técnico/a", 2, "29689.98", "2120.71", "1002.16"),
        ("3", "Técnica/o auxiliar", 3, "26768.79", "1912.06", "913.80"),
        ("4", "Empleado/a", 4, "23930.65", "1709.33", "841.22"),
        ("5", "Operaria/o", 5, "22263.68", "1590.26", "26.46"),
        ("6", "Empleado/a auxiliar", 6, "22030.78", "1573.63", "781.71"),
        ("7", "Operaria/o auxiliar", 7, "20687.47", "1477.68", "25.28"),
    ]
    for grupo, nombre, grupo_cot, anual, mensual, quinquenio in grupos_metal:
        categoria = CategoriaProfesional(
            convenio_id=metal.id, grupo=grupo, nombre=nombre, grupo_cotizacion=grupo_cot
        )
        db.add(categoria)
        db.flush()
        db.add(
            ConvenioTablaSalarial(
                categoria_id=categoria.id,
                anio=2026,
                salario_convenio_anual=Decimal(anual),
                salario_convenio_mensual=Decimal(mensual),
                valor_quinquenio_o_trienio=Decimal(quinquenio),
                plus_convenio_mensual=Decimal("0"),
                vigente_desde=VIGENTE_DESDE_2026,
            )
        )

    # ---- 2) Construcción (grupos del VIII Convenio General; salarios de EJEMPLO) ----
    construccion = Convenio(
        nombre="Construcción (VIII Convenio General del Sector) — EJEMPLO",
        ambito="estatal (remite a tablas provinciales)",
        provincia=None,
        codigo_convenio="99005585011900",
        fuente="BOE núm. 115, 12/05/2026 (VIII CGSC); SIN tabla salarial propia — sustituir por convenio provincial",
        numero_pagas=14,
        jornada_anual_horas=Decimal("1738"),
        notas="EJEMPLO: el convenio general no fija salarios. Sustituir por la tabla salarial provincial vigente antes de usar en producción.",
    )
    db.add(construccion)
    db.flush()

    grupos_construccion = [
        ("1", "Nivel I - Ingenierías y licenciaturas", 1, "31000.00", "2214.29"),
        ("4", "Nivel IV - Encargado/a general", 4, "24500.00", "1750.00"),
        ("6", "Nivel VI - Oficial de 1ª", 6, "21500.00", "1535.71"),
        ("8", "Nivel VIII - Peón ordinario", 7, "19200.00", "1371.43"),
    ]
    for grupo, nombre, grupo_cot, anual, mensual in grupos_construccion:
        categoria = CategoriaProfesional(
            convenio_id=construccion.id, grupo=grupo, nombre=nombre, grupo_cotizacion=grupo_cot
        )
        db.add(categoria)
        db.flush()
        db.add(
            ConvenioTablaSalarial(
                categoria_id=categoria.id,
                anio=2026,
                salario_convenio_anual=Decimal(anual),
                salario_convenio_mensual=Decimal(mensual),
                plus_convenio_mensual=Decimal("0"),
                vigente_desde=VIGENTE_DESDE_2026,
            )
        )

    # ---- 3) Comercio Madrid — EJEMPLO ----
    comercio = Convenio(
        nombre="Comercio (Madrid) — EJEMPLO",
        ambito="provincial",
        provincia="Madrid",
        codigo_convenio=None,
        fuente="EJEMPLO orientativo — sustituir por el convenio de comercio vigente en BOCM",
        numero_pagas=14,
        jornada_anual_horas=Decimal("1800"),
        notas="EJEMPLO con valores orientativos. Verificar tablas oficiales antes de usar en producción.",
    )
    db.add(comercio)
    db.flush()

    grupos_comercio = [
        ("1", "Jefe/a de división", 2, "26000.00", "1857.14"),
        ("3", "Jefe/a de sección", 4, "21500.00", "1535.71"),
        ("5", "Dependiente/a", 6, "18500.00", "1321.43"),
        ("7", "Auxiliar / Mozo/a", 7, "16800.00", "1200.00"),
    ]
    for grupo, nombre, grupo_cot, anual, mensual in grupos_comercio:
        categoria = CategoriaProfesional(
            convenio_id=comercio.id, grupo=grupo, nombre=nombre, grupo_cotizacion=grupo_cot
        )
        db.add(categoria)
        db.flush()
        db.add(
            ConvenioTablaSalarial(
                categoria_id=categoria.id,
                anio=2026,
                salario_convenio_anual=Decimal(anual),
                salario_convenio_mensual=Decimal(mensual),
                plus_convenio_mensual=Decimal("0"),
                vigente_desde=VIGENTE_DESDE_2026,
            )
        )

    db.commit()
