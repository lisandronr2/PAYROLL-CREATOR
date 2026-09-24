from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PresupuestoItems(Base):
    """Presupuesto de proyecto calculado a partir de partidas de catálogo
    (precio por unidad de obra) en lugar de personal por horas — pensado
    para trabajos que se cotizan por partidas/ítems (ej. instalaciones de
    comunicaciones): cableado, canalización, CCTV, red, etc. El precio de
    cada línea ya incluye el margen de la partida, así que aquí solo se
    suman las líneas y se aplica el IVA — no hay gastos generales ni
    margen global como en el presupuesto por personal."""
    __tablename__ = "presupuestos_items"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)

    nombre = Column(String, nullable=False)  # referencia / nombre del proyecto
    cliente_nombre = Column(String, nullable=True)
    cliente_nif = Column(String, nullable=True)
    fecha = Column(Date, nullable=False)
    notas = Column(Text, nullable=True)

    iva_pct = Column(Numeric(6, 3), nullable=False)

    subtotal = Column(Numeric(12, 2), nullable=False, default=0)  # suma de importes de línea (con margen ya incluido)
    iva_importe = Column(Numeric(12, 2), nullable=False, default=0)
    precio_total_cliente = Column(Numeric(12, 2), nullable=False, default=0)

    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    empresa = relationship("Empresa")
    lineas = relationship("PresupuestoItemsLinea", back_populates="presupuesto", cascade="all, delete-orphan")


class PresupuestoItemsLinea(Base):
    """Línea de presupuesto por items: referencia a una partida de catálogo,
    pero con los datos de la partida "fotografiados" en el momento de
    añadirla (nombre, unidad, coste directo, margen y precio de venta) para
    que cambios futuros en el catálogo no alteren presupuestos ya creados."""
    __tablename__ = "presupuesto_items_lineas"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos_items.id"), nullable=False)
    partida_id = Column(Integer, ForeignKey("partidas_catalogo.id"), nullable=True)

    familia = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    unidad = Column(String, nullable=False)

    coste_directo_unitario = Column(Numeric(10, 2), nullable=False, default=0)
    margen_pct = Column(Numeric(6, 2), nullable=False, default=0)
    precio_unitario = Column(Numeric(10, 2), nullable=False, default=0)  # precio de venta unitario (con margen)

    cantidad = Column(Numeric(10, 2), nullable=False, default=1)
    descuento_pct = Column(Numeric(6, 2), nullable=False, default=0)
    importe = Column(Numeric(12, 2), nullable=False, default=0)  # precio_unitario * cantidad * (1 - descuento_pct/100)

    presupuesto = relationship("PresupuestoItems", back_populates="lineas")
    partida = relationship("PartidaCatalogo")
