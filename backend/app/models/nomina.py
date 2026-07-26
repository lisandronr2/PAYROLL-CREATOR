from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Numeric, Date, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Nomina(Base):
    __tablename__ = "nominas"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    periodo_anio = Column(Integer, nullable=False)
    periodo_mes = Column(Integer, nullable=False)
    tipo = Column(String, default="mensual")  # mensual, finiquito, paga_extra

    dias_naturales_periodo = Column(Integer, nullable=False, default=30)
    dias_trabajados = Column(Integer, nullable=False, default=30)
    horas_extra = Column(Numeric(6, 2), default=0)
    dias_it = Column(Integer, default=0)
    dias_vacaciones = Column(Integer, default=0)

    total_devengado = Column(Numeric(10, 2), nullable=False, default=0)
    total_deducciones = Column(Numeric(10, 2), nullable=False, default=0)
    liquido_a_percibir = Column(Numeric(10, 2), nullable=False, default=0)
    base_cotizacion_comun = Column(Numeric(10, 2), nullable=False, default=0)
    base_sujeta_irpf = Column(Numeric(10, 2), nullable=False, default=0)
    coste_empresa_total = Column(Numeric(10, 2), nullable=False, default=0)
    total_dietas_exentas = Column(Numeric(10, 2), nullable=False, default=0)

    generada_en = Column(DateTime(timezone=True), server_default=func.now())
    pdf_path = Column(String, nullable=True)

    contrato = relationship("Contrato")
    lineas = relationship("NominaLinea", back_populates="nomina", cascade="all, delete-orphan")


class NominaLinea(Base):
    """Cada línea del desglose (devengo, cotización, deducción) con su base legal."""
    __tablename__ = "nomina_lineas"

    id = Column(Integer, primary_key=True, index=True)
    nomina_id = Column(Integer, ForeignKey("nominas.id"), nullable=False)
    bloque = Column(String, nullable=False)  # devengo, cotizacion_trabajador, cotizacion_empresa, deduccion
    concepto = Column(String, nullable=False)
    base = Column(Numeric(10, 2), nullable=True)
    tipo_pct = Column(Numeric(6, 3), nullable=True)
    importe = Column(Numeric(10, 2), nullable=False)
    referencia_legal = Column(Text, nullable=True)
    orden = Column(Integer, default=0)
    # Solo relevante en bloque "devengo": si computa en la base de cotización SS.
    cotiza = Column(Boolean, nullable=False, default=True)

    nomina = relationship("Nomina", back_populates="lineas")
