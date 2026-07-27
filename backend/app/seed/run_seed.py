"""Ejecutar con: python -m app.seed.run_seed"""
from app.database import Base, SessionLocal, engine
from app import models  # noqa: F401 (registra los modelos en Base.metadata)
from app.seed.parametros_legales import seed_parametros_legales, corregir_parametros_legales
from app.seed.tabla_irpf import seed_tabla_irpf
from app.seed.convenios import seed_convenios, seed_convenio_dietas
from app.seed.usuarios import seed_usuario_admin
from app.migrations_ligeras import aplicar_migraciones_ligeras


def main() -> None:
    Base.metadata.create_all(bind=engine)
    aplicar_migraciones_ligeras(engine)
    db = SessionLocal()
    try:
        seed_parametros_legales(db)
        corregir_parametros_legales(db)
        seed_tabla_irpf(db)
        seed_convenios(db)
        seed_convenio_dietas(db)
        seed_usuario_admin(db)
        print("Seed completado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
