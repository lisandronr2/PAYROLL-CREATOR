"""Ejecutar con: python -m app.seed.run_seed"""
from app.database import Base, SessionLocal, engine
from app import models  # noqa: F401 (registra los modelos en Base.metadata)
from app.seed.parametros_legales import seed_parametros_legales
from app.seed.tabla_irpf import seed_tabla_irpf
from app.seed.convenios import seed_convenios
from app.seed.usuarios import seed_usuario_admin


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_parametros_legales(db)
        seed_tabla_irpf(db)
        seed_convenios(db)
        seed_usuario_admin(db)
        print("Seed completado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
