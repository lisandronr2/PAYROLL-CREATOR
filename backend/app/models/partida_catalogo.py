from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.database import Base


class PartidaCatalogo(Base):
    """Partida de catálogo de precios (mano de obra + material + medios
    auxiliares por unidad), agrupada por familia (Cableado, CCTV, Red...).
    Es la base de datos de precios usada por "Presupuesto por items": cada
    partida ya lleva su margen aplicado en precio_venta, que es el importe
    final que se factura por unidad — no se le vuelve a aplicar gastos
    generales/margen global como en el presupuesto por personal."""
    __tablename__ = "partidas_catalogo"

    id = Column(Integer, primary_key=True, index=True)
    familia = Column(String, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    unidad = Column(String, nullable=False)  # m, ud, h, día...

    precio_coste_mo = Column(Numeric(10, 2), nullable=False, default=0)
    precio_material = Column(Numeric(10, 2), nullable=False, default=0)
    precio_medios_aux = Column(Numeric(10, 2), nullable=False, default=0)
    coste_directo = Column(Numeric(10, 2), nullable=False, default=0)  # suma de los 3 anteriores

    margen_pct = Column(Numeric(6, 2), nullable=False, default=20)
    precio_venta = Column(Numeric(10, 2), nullable=False, default=0)  # coste_directo * (1 + margen_pct/100)

    observaciones = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)

    creado_en = Column(DateTime(timezone=True), server_default=func.now())
