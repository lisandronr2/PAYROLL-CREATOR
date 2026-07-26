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
]


def aplicar_migraciones_ligeras(engine: Engine) -> None:
    with engine.connect() as conn:
        for tabla, columna, definicion in COLUMNAS_NUEVAS:
            try:
                conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"))
                conn.commit()
            except Exception:
                conn.rollback()
