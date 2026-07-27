from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True, index=True)
    trabajador_id = Column(Integer, ForeignKey("trabajadores.id"), nullable=False)
    convenio_id = Column(Integer, ForeignKey("convenios.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias_profesionales.id"), nullable=False)

    tipo_contrato = Column(String, nullable=False)  # indefinido, temporal, formacion, practicas
    jornada_porcentaje = Column(Numeric(5, 2), default=100)  # 100 = completa, 50 = media jornada
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)

    puesto_trabajo = Column(String, nullable=True)  # p.ej. "Instalador" (distinto de la categoría de convenio)
    seccion = Column(String, nullable=True)

    salario_pactado_mensual = Column(Numeric(10, 2), nullable=True)  # si difiere del convenio (mejora)
    # Complemento fijo mensual adicional al salario de convenio (mejora
    # voluntaria pactada), sujeto a cotización e IRPF igual que el salario.
    complemento_mensual = Column(Numeric(10, 2), nullable=False, default=0)
    pagas_extra_prorrateadas = Column(Boolean, default=False)
    fecha_antiguedad = Column(Date, nullable=True)  # para trienios/quinquenios, si distinta de fecha_inicio

    trabajador = relationship("Trabajador", back_populates="contratos")
    convenio = relationship("Convenio")
    categoria = relationship("CategoriaProfesional")
