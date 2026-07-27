from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    razon_social = Column(String, nullable=False)
    cif = Column(String, nullable=False, unique=True)
    direccion = Column(String)
    cnae = Column(String)
    codigo_cuenta_cotizacion = Column(String)  # CCC de la Seguridad Social
    # Tipo de cotización por contingencias profesionales (AT y EP), 100% a
    # cargo de la empresa. Depende del CNAE/epígrafe de actividad según la
    # tarifa de primas (DA 61ª LGSS, RD-ley 16/2025) — verificar el tipo
    # exacto aplicable a esta empresa; 1.50 es un valor de partida genérico.
    tipo_at_ep_pct = Column(Numeric(5, 3), nullable=False, default=1.50)
    convenio_id = Column(Integer, index=True, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    trabajadores = relationship("Trabajador", back_populates="empresa")
