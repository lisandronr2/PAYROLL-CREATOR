from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app import models  # noqa: F401
from app.routers import empresas, trabajadores, contratos, convenios, nominas, auth, admin
from app.seed.parametros_legales import seed_parametros_legales
from app.seed.tabla_irpf import seed_tabla_irpf
from app.seed.convenios import seed_convenios
from app.seed.usuarios import seed_usuario_admin

app = FastAPI(title="Payroll Creator API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_parametros_legales(db)
        seed_tabla_irpf(db)
        seed_convenios(db)
        seed_usuario_admin(db)
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(empresas.router)
app.include_router(trabajadores.router)
app.include_router(contratos.router)
app.include_router(convenios.router)
app.include_router(nominas.router)


@app.get("/health")
def health():
    return {"status": "ok"}
