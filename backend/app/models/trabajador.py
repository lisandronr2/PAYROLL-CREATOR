from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Trabajador(Base):
    __tablename__ = "trabajadores"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nombre = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    nif = Column(String, nullable=False, unique=True)
    numero_afiliacion_ss = Column(String)
    fecha_nacimiento = Column(Date)
    fecha_alta = Column(Date, nullable=False)
    fecha_baja = Column(Date, nullable=True)

    # Situación IRPF (art. 80-88 Reglamento IRPF)
    situacion_familiar = Column(String, default="soltero")  # soltero, casado, etc.
    hijos_menores_25 = Column(Integer, default=0)
    grado_discapacidad = Column(Integer, default=0)  # 0, 33, 65...

    iban = Column(String)
    activo = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="trabajadores")
    contratos = relationship("Contrato", back_populates="trabajador")
