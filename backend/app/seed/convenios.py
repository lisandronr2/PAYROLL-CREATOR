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

from app.models.convenio import Convenio, CategoriaProfesional, ConvenioDieta, ConvenioTablaSalarial

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


def seed_convenio_dietas(db: Session) -> None:
    """
    Se ejecuta de forma independiente de seed_convenios() para que también
    añada las dietas si el convenio ya existía de un despliegue anterior
    (antes de que existiera esta tabla).
    """
    if db.query(ConvenioDieta).first() is not None:
        return

    dietas_por_convenio = {
        # Metal Madrid: valores REALES, Acta Comisión Negociadora 21/01/2026 (BOCM núm. 59)
        "Industria, Servicios e Instalaciones del Metal de Madrid": ("12.14", "59.17", "47.36"),
        # Resto: EJEMPLO orientativo, verificar tablas oficiales del convenio aplicable
        "Construcción (VIII Convenio General del Sector) — EJEMPLO": ("10.00", "40.00", "60.00"),
        "Comercio (Madrid) — EJEMPLO": ("9.00", "35.00", "55.00"),
    }

    for nombre, (media, corta, larga) in dietas_por_convenio.items():
        convenio = db.query(Convenio).filter(Convenio.nombre == nombre).first()
        if convenio is None:
            continue
        db.add(
            ConvenioDieta(
                convenio_id=convenio.id,
                anio=2026,
                media_dieta=Decimal(media),
                dieta_completa_corta=Decimal(corta),
                dieta_completa_larga=Decimal(larga),
                vigente_desde=VIGENTE_DESDE_2026,
            )
        )
    db.commit()


# Subniveles reales del Convenio Metal Madrid, tomados del Anexo II
# ("Grupos Profesionales" — equivalencias orientativas de categorías del
# convenio anterior integradas en cada Grupo) del texto consolidado
# 2024-2026 (AECIM/CCOO/UGT). El salario de cada subnivel es el de su Grupo
# Profesional "padre" (el convenio no publica un salario distinto por
# subnivel, solo por Grupo) — lo que cambia es la categoría/oficio concreto
# que se muestra en el contrato y la nómina.
#
# grupo_cotizacion: se usa el grupo de cotización a la SS real y reconocible
# para los oficios manuales (8 = Oficiales de 1ª y 2ª, 9 = Oficiales de 3ª y
# Especialistas, 10 = Peones), y se mantiene el número de Grupo Profesional
# como aproximación para el resto de categorías (empleados/técnicos), igual
# que en las categorías genéricas ya existentes — ver docs/LEGAL_DISCLAIMER.md.
SUBNIVELES_METAL = {
    "2": [
        ("2.1", "Jefe/a de Taller", 2),
        ("2.2", "Analista Informático/a", 2),
        ("2.3", "Graduado/a Social / Diplomado/a en Relaciones Laborales", 2),
        ("2.4", "Ayudante Técnico Sanitario / Diplomado/a en Enfermería", 2),
    ],
    "3": [
        ("3.1", "Delineante Proyectista/Dibujante", 3),
        ("3.2", "Jefe/a de Organización de 1ª", 3),
        ("3.3", "Jefe/a de Laboratorio de 2ª", 3),
        ("3.4", "Jefe/a de 2ª Administrativo/a", 3),
        ("3.5", "Programador/a Informático/a", 3),
        ("3.6", "Maestro/a Industrial", 3),
        ("3.7", "Maestro/a de Taller de 1ª", 3),
        ("3.8", "Contramaestre", 3),
        ("3.9", "Maestro/a de Taller de 2ª", 3),
    ],
    "4": [
        ("4.1", "Delineante de 1ª", 4),
        ("4.2", "Delineante de 2ª", 4),
        ("4.3", "Operador/a Informático/a", 4),
        ("4.4", "Analista de Laboratorio de 1ª", 4),
        ("4.5", "Técnico/a de Organización de 1ª", 4),
        ("4.6", "Técnico/a de Organización de 2ª", 4),
        ("4.7", "Oficial Administrativo/a de 1ª", 4),
        ("4.8", "Oficial Administrativo/a de 2ª", 4),
        ("4.9", "Conductor/a", 4),
        ("4.10", "Comercial", 4),
        ("4.11", "Encargado/a de Sección de Taller", 4),
    ],
    "5": [
        ("5.1", "Oficial de 1ª (de oficio)", 8),
        ("5.2", "Oficial de 2ª (de oficio)", 8),
        ("5.3", "Capataz de Especialistas y Peones Ordinarios", 3),
    ],
    "6": [
        ("6.1", "Conserje", 6),
        ("6.2", "Almacenero/a", 6),
        ("6.3", "Auxiliar (oficina, laboratorio, administrativo/a u organización)", 6),
        ("6.4", "Analista de Laboratorio de 2ª", 6),
        ("6.5", "Ordenanza", 6),
        ("6.6", "Portero/a", 6),
        ("6.7", "Telefonista", 6),
    ],
    "7": [
        ("7.1", "Peón/a", 10),
        ("7.2", "Mozo/a Especialista de Almacén", 9),
        ("7.3", "Especialista", 9),
        ("7.4", "Oficial de 3ª (de taller)", 9),
    ],
}


def seed_subniveles_metal(db: Session) -> None:
    """
    Añade los subniveles/categorías reales del Convenio Metal Madrid dentro
    de cada Grupo Profesional (ej. "5.1 Oficial de 1ª", "7.4 Oficial de 3ª"),
    reutilizando el salario del Grupo "padre" ya sembrado. Idempotente: solo
    crea los que aún no existan (comprueba por convenio_id + grupo).
    """
    convenio = (
        db.query(Convenio)
        .filter(Convenio.nombre == "Industria, Servicios e Instalaciones del Metal de Madrid")
        .first()
    )
    if convenio is None:
        return

    for grupo_padre, subniveles in SUBNIVELES_METAL.items():
        categoria_padre = (
            db.query(CategoriaProfesional)
            .filter(CategoriaProfesional.convenio_id == convenio.id, CategoriaProfesional.grupo == grupo_padre)
            .first()
        )
        if categoria_padre is None:
            continue
        tabla_padre = (
            db.query(ConvenioTablaSalarial)
            .filter(ConvenioTablaSalarial.categoria_id == categoria_padre.id)
            .order_by(ConvenioTablaSalarial.vigente_desde.desc())
            .first()
        )
        if tabla_padre is None:
            continue

        for codigo, nombre, grupo_cotizacion in subniveles:
            ya_existe = (
                db.query(CategoriaProfesional)
                .filter(CategoriaProfesional.convenio_id == convenio.id, CategoriaProfesional.grupo == codigo)
                .first()
            )
            if ya_existe is not None:
                continue

            subnivel = CategoriaProfesional(
                convenio_id=convenio.id,
                grupo=codigo,
                nombre=nombre,
                grupo_cotizacion=grupo_cotizacion,
            )
            db.add(subnivel)
            db.flush()
            db.add(
                ConvenioTablaSalarial(
                    categoria_id=subnivel.id,
                    anio=tabla_padre.anio,
                    salario_convenio_anual=tabla_padre.salario_convenio_anual,
                    salario_convenio_mensual=tabla_padre.salario_convenio_mensual,
                    base_calculo_complementos_mensual=tabla_padre.base_calculo_complementos_mensual,
                    valor_quinquenio_o_trienio=tabla_padre.valor_quinquenio_o_trienio,
                    plus_convenio_mensual=tabla_padre.plus_convenio_mensual,
                    vigente_desde=tabla_padre.vigente_desde,
                    vigente_hasta=tabla_padre.vigente_hasta,
                )
            )

    db.commit()
