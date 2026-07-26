from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


class HistorialModificacion(Base):
    """Registro de auditoría de cambios sobre entidades sensibles (contratos, parámetros legales, convenios)."""
    __tablename__ = "historial_modificaciones"

    id = Column(Integer, primary_key=True, index=True)
    entidad = Column(String, nullable=False)  # p.ej. "Contrato", "ParametroLegal"
    entidad_id = Column(Integer, nullable=False)
    accion = Column(String, nullable=False)  # creado, actualizado, eliminado
    detalle = Column(Text, nullable=True)
    usuario = Column(String, nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
