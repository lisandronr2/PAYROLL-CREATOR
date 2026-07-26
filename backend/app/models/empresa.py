from sqlalchemy import Column, Integer, String, DateTime
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
    convenio_id = Column(Integer, index=True, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    trabajadores = relationship("Trabajador", back_populates="empresa")
