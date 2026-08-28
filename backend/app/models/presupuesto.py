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
    # coste_directo_personal es un campo heredado de la primera versión (antes
    # de separar dietas de mano de obra): la columna ya existe como NOT NULL
    # en despliegues anteriores, así que se sigue rellenando (con la suma de
    # mano_obra + dietas) para no romper esa restricción — no se usa para
    # ningún cálculo nuevo, solo por compatibilidad con la tabla ya creada.
    coste_directo_personal = Column(Numeric(12, 2), nullable=False, default=0)
    coste_directo_mano_obra = Column(Numeric(12, 2), nullable=False, default=0)
    coste_directo_dietas = Column(Numeric(12, 2), nullable=False, default=0)
    coste_directo_otros = Column(Numeric(12, 2), nullable=False, default=0)  # materiales/otros costes sueltos
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
    """Un perfil de personal dentro del presupuesto: categoría del convenio
    (solo como referencia/etiqueta), cuántas personas, precio/hora pactado,
    días de dedicación al proyecto (jornadas normales de 8h) y dietas
    estimadas para todo el periodo (no por mes, y sí tomadas del convenio)."""
    __tablename__ = "presupuesto_lineas_personal"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias_profesionales.id"), nullable=False)

    cantidad_personas = Column(Integer, nullable=False, default=1)
    precio_hora = Column(Numeric(8, 2), nullable=False, default=0)  # €/hora pactado, define el usuario
    dias_dedicacion = Column(Numeric(6, 2), nullable=False)  # días de dedicación (jornadas de 8h)

    # Campos heredados de la versión anterior (cálculo basado en el salario
    # de convenio): ya no se usan para calcular nada — ver
    # app/engine/presupuesto.py — pero la columna sigue siendo NOT NULL en la
    # tabla ya desplegada, así que se rellenan con un valor fijo al crear.
    jornada_porcentaje = Column(Numeric(5, 2), nullable=False, default=100)
    pagas_extra_prorrateadas = Column(Boolean, nullable=False, default=True)
    complemento_mensual = Column(Numeric(10, 2), nullable=False, default=0)

    numero_medias_dietas = Column(Integer, nullable=False, default=0)
    numero_dietas_completas_cortas = Column(Integer, nullable=False, default=0)
    numero_dietas_completas_largas = Column(Integer, nullable=False, default=0)

    # Resultado calculado (por una persona, y total con la cantidad de personas).
    coste_unitario = Column(Numeric(12, 2), nullable=False, default=0)
    coste_total_linea = Column(Numeric(12, 2), nullable=False, default=0)
    # Desglose del total de la línea: mano de obra sola vs dietas solas.
    coste_mano_obra_total = Column(Numeric(12, 2), nullable=False, default=0)
    coste_dietas_total = Column(Numeric(12, 2), nullable=False, default=0)

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
