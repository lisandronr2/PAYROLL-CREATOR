from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Presupuesto(Base):
    """
    Presupuesto de proyecto: estima el coste real de mano de obra (según el
    convenio elegido) más materiales/otros costes, aplica gastos generales
    de estructura y margen de beneficio, y con IVA calcula el precio final
    a ofertar al cliente. Misma lógica que "PEM + Gastos Generales +
    Beneficio Industrial = PEC + IVA" usada en licitaciones de obra.
    """
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    convenio_id = Column(Integer, ForeignKey("convenios.id"), nullable=False)

    nombre = Column(String, nullable=False)  # referencia / nombre del proyecto
    cliente_nombre = Column(String, nullable=True)
    cliente_nif = Column(String, nullable=True)
    fecha = Column(Date, nullable=False)
    notas = Column(Text, nullable=True)

    # % aplicados (si el usuario no indica uno propio al crear, se copian los
    # valores por defecto de ParametroNegocio en ese momento).
    margen_beneficio_pct = Column(Numeric(6, 3), nullable=False)
    gastos_generales_pct = Column(Numeric(6, 3), nullable=False)
    iva_pct = Column(Numeric(6, 3), nullable=False)

    # Totales calculados (se recalculan por completo cada vez que se guarda).
    coste_directo_personal = Column(Numeric(12, 2), nullable=False, default=0)
    coste_directo_otros = Column(Numeric(12, 2), nullable=False, default=0)
    coste_directo_total = Column(Numeric(12, 2), nullable=False, default=0)
    gastos_generales_importe = Column(Numeric(12, 2), nullable=False, default=0)
    coste_total = Column(Numeric(12, 2), nullable=False, default=0)
    margen_importe = Column(Numeric(12, 2), nullable=False, default=0)
    precio_venta = Column(Numeric(12, 2), nullable=False, default=0)  # sin IVA
    iva_importe = Column(Numeric(12, 2), nullable=False, default=0)
    precio_total_cliente = Column(Numeric(12, 2), nullable=False, default=0)

    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    empresa = relationship("Empresa")
    convenio = relationship("Convenio")
    lineas_personal = relationship(
        "PresupuestoLineaPersonal", back_populates="presupuesto", cascade="all, delete-orphan"
    )
    lineas_otros = relationship(
        "PresupuestoLineaOtroCoste", back_populates="presupuesto", cascade="all, delete-orphan"
    )


class PresupuestoLineaPersonal(Base):
    """Un perfil de personal dentro del presupuesto: categoría del convenio,
    cuántas personas, jornada, días de dedicación al proyecto y dietas
    estimadas para todo el periodo (no por mes)."""
    __tablename__ = "presupuesto_lineas_personal"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias_profesionales.id"), nullable=False)

    cantidad_personas = Column(Integer, nullable=False, default=1)
    jornada_porcentaje = Column(Numeric(5, 2), nullable=False, default=100)
    dias_dedicacion = Column(Numeric(6, 2), nullable=False)  # días naturales de dedicación al proyecto
    pagas_extra_prorrateadas = Column(Boolean, nullable=False, default=True)
    complemento_mensual = Column(Numeric(10, 2), nullable=False, default=0)  # mejora voluntaria, si aplica

    numero_medias_dietas = Column(Integer, nullable=False, default=0)
    numero_dietas_completas_cortas = Column(Integer, nullable=False, default=0)
    numero_dietas_completas_largas = Column(Integer, nullable=False, default=0)

    # Resultado calculado (por una persona, y total con la cantidad de personas).
    coste_unitario = Column(Numeric(12, 2), nullable=False, default=0)
    coste_total_linea = Column(Numeric(12, 2), nullable=False, default=0)

    presupuesto = relationship("Presupuesto", back_populates="lineas_personal")
    categoria = relationship("CategoriaProfesional")


class PresupuestoLineaOtroCoste(Base):
    """Línea suelta de coste directo no laboral: materiales, alquiler de
    maquinaria, subcontratas, etc."""
    __tablename__ = "presupuesto_lineas_otros"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    concepto = Column(String, nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False, default=1)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    importe = Column(Numeric(12, 2), nullable=False)  # cantidad * precio_unitario

    presupuesto = relationship("Presupuesto", back_populates="lineas_otros")
