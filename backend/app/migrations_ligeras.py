"""
Migraciones ligeras para columnas nuevas en tablas ya existentes.

El proyecto usa `Base.metadata.create_all()` para crear tablas que faltan,
pero eso no añade columnas nuevas a tablas que ya existen en una base de
datos desplegada. Este módulo aplica esos `ALTER TABLE` de forma segura
(ignora el error si la columna ya existe) tanto en SQLite (dev) como en
Postgres (producción/Supabase).

Si el proyecto crece mucho más, esto debería sustituirse por Alembic.
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine

# (tabla, columna, definición SQL de la columna)
COLUMNAS_NUEVAS = [
    ("nominas", "total_dietas_exentas", "NUMERIC(10, 2) NOT NULL DEFAULT 0"),
    ("nomina_lineas", "cotiza", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("empresas", "tipo_at_ep_pct", "NUMERIC(5, 3) NOT NULL DEFAULT 1.50"),
    ("empresas", "poblacion", "VARCHAR"),
    ("contratos", "puesto_trabajo", "VARCHAR"),
    ("contratos", "seccion", "VARCHAR"),
    ("contratos", "complemento_mensual", "NUMERIC(10, 2) NOT NULL DEFAULT 0"),
    ("nomina_lineas", "cantidad", "NUMERIC(8, 3)"),
    ("usuarios", "reset_token_hash", "VARCHAR"),
    ("usuarios", "reset_token_expira", "TIMESTAMP"),
    ("nominas", "horas_extra_nocturnas", "NUMERIC(6, 2) DEFAULT 0"),
    ("nominas", "horas_nocturnas_ordinarias", "NUMERIC(6, 2) DEFAULT 0"),
    ("nominas", "dias_festivos_trabajados", "INTEGER DEFAULT 0"),
    ("nominas", "anticipos", "NUMERIC(10, 2) DEFAULT 0"),
    ("nominas", "embargo_mensual", "NUMERIC(10, 2) DEFAULT 0"),
    ("nominas", "numero_medias_dietas", "INTEGER DEFAULT 0"),
    ("nominas", "numero_dietas_completas_cortas", "INTEGER DEFAULT 0"),
    ("nominas", "numero_dietas_completas_largas", "INTEGER DEFAULT 0"),
]


def aplicar_migraciones_ligeras(engine: Engine) -> None:
    with engine.connect() as conn:
        for tabla, columna, definicion in COLUMNAS_NUEVAS:
            try:
                conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"))
                conn.commit()
            except Exception:
                conn.rollback()
