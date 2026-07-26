from sqlalchemy import Column, Integer, Date, String, Boolean

from app.database import Base


class CalendarioLaboral(Base):
    __tablename__ = "calendario_laboral"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True)
    provincia = Column(String, nullable=True)  # null = festivo nacional
    descripcion = Column(String, nullable=False)
    es_festivo = Column(Boolean, default=True)
