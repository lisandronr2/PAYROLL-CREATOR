import json

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Liquidacion(Base):
    """Liquidación (finiquito) guardada. Conserva los datos de entrada para
    poder editarla y recalcularla, y el resultado (líneas y totales) tal como
    se calculó, para que el PDF no cambie si luego se modifican el convenio,
    el contrato o el trabajador."""
    __tablename__ = "liquidaciones"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    trabajador_id = Column(Integer, ForeignKey("trabajadores.id"), nullable=False)

    # Datos del trabajador y del contrato en el momento de calcular.
    trabajador_nombre = Column(String, nullable=False)
    trabajador_nif = Column(String, nullable=False)
    convenio_nombre = Column(String, nullable=False)
    categoria = Column(String, nullable=False)

    # Datos de entrada.
    motivo = Column(String, nullable=False)
    motivo_texto = Column(String, nullable=False)
    fecha_ingreso = Column(Date, nullable=False)
    fecha_baja = Column(Date, nullable=False)
    dias_preaviso_exigidos = Column(Integer, nullable=False, default=0)
    dias_preaviso_trabajados = Column(Integer, nullable=False, default=0)
    vacaciones_disfrutadas = Column(Numeric(8, 2), nullable=False, default=0)
    unidad_vacaciones = Column(String, nullable=False, default="naturales")
    vacaciones_pendientes_anteriores = Column(Numeric(8, 2), nullable=False, default=0)
    otras_cantidades = Column(Numeric(12, 2), nullable=False, default=0)
    indemnizacion_pactada = Column(Numeric(12, 2), nullable=False, default=0)
    descuentos = Column(Numeric(12, 2), nullable=False, default=0)
    notas = Column(Text, nullable=True)

    # Reglas del convenio usadas.
    vacaciones_dias_naturales = Column(Integer, nullable=False, default=30)
    vacaciones_dias_laborables = Column(Integer, nullable=True)

    # Resultado.
    antiguedad_texto = Column(String, nullable=False, default="")
    salario_diario_indemnizacion = Column(Numeric(12, 4), nullable=False, default=0)
    salario_diario_preaviso = Column(Numeric(12, 4), nullable=False, default=0)
    total_ingresos = Column(Numeric(12, 2), nullable=False, default=0)
    indemnizacion_legal = Column(Numeric(12, 2), nullable=False, default=0)
    indemnizacion_exenta = Column(Numeric(12, 2), nullable=False, default=0)
    base_cotizacion = Column(Numeric(12, 2), nullable=False, default=0)
    base_irpf = Column(Numeric(12, 2), nullable=False, default=0)
    cotizacion_trabajador = Column(Numeric(12, 2), nullable=False, default=0)
    tipo_irpf_pct = Column(Numeric(6, 2), nullable=False, default=0)
    retencion_irpf = Column(Numeric(12, 2), nullable=False, default=0)
    total_descuentos = Column(Numeric(12, 2), nullable=False, default=0)
    total_deducciones = Column(Numeric(12, 2), nullable=False, default=0)
    liquido_a_percibir = Column(Numeric(12, 2), nullable=False, default=0)
    cuota_empresa_ss = Column(Numeric(12, 2), nullable=False, default=0)
    coste_empresa_total = Column(Numeric(12, 2), nullable=False, default=0)
    avisos_json = Column(Text, nullable=False, default="[]")

    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    contrato = relationship("Contrato")
    lineas = relationship(
        "LiquidacionLinea",
        back_populates="liquidacion",
        cascade="all, delete-orphan",
        order_by="LiquidacionLinea.orden",
    )

    @property
    def avisos(self) -> list[str]:
        return json.loads(self.avisos_json or "[]")


class LiquidacionLinea(Base):
    __tablename__ = "liquidacion_lineas"

    id = Column(Integer, primary_key=True, index=True)
    liquidacion_id = Column(Integer, ForeignKey("liquidaciones.id"), nullable=False)
    orden = Column(Integer, nullable=False, default=0)
    bloque = Column(String, nullable=False)  # devengo | indemnizacion | descuento | deduccion
    concepto = Column(String, nullable=False)
    importe = Column(Numeric(12, 2), nullable=False)
    detalle = Column(Text, nullable=True)
    referencia_legal = Column(Text, nullable=True)
    cotiza = Column(Boolean, nullable=False, default=False)
    tributa = Column(Boolean, nullable=False, default=False)

    liquidacion = relationship("Liquidacion", back_populates="lineas")
