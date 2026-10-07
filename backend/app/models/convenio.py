from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Date, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Convenio(Base):
    __tablename__ = "convenios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)  # p.ej. "Industria, Servicios e Instalaciones del Metal de Madrid"
    ambito = Column(String)  # provincial, autonomico, estatal, empresa
    provincia = Column(String)
    codigo_convenio = Column(String)  # código oficial REGCON
    fuente = Column(String)  # referencia BOE/BOCM
    numero_pagas = Column(Integer, default=14)
    jornada_anual_horas = Column(Numeric(7, 2), default=1800)  # jornada máxima anual pactada
    notas = Column(Text)  # avisos de vigencia / verificación

    # Reglas del convenio que usa la liquidación/finiquito. Nulas = no
    # informadas: se aplica el mínimo legal (30 días naturales de vacaciones,
    # art. 38 ET) y 15 días de preaviso de cese voluntario (uso habitual).
    vacaciones_dias_naturales = Column(Integer, nullable=True)
    vacaciones_dias_laborables = Column(Integer, nullable=True)
    preaviso_cese_dias_tecnicos = Column(Integer, nullable=True)  # personal técnico y titulado
    preaviso_cese_dias_resto = Column(Integer, nullable=True)


class CategoriaProfesional(Base):
    __tablename__ = "categorias_profesionales"

    id = Column(Integer, primary_key=True, index=True)
    convenio_id = Column(Integer, ForeignKey("convenios.id"), nullable=False)
    grupo = Column(String, nullable=False)  # p.ej. "1", "Grupo 5"
    nombre = Column(String, nullable=False)  # p.ej. "Operaria/o"
    grupo_cotizacion = Column(Integer, nullable=False)  # 1-11, grupo de cotización SS

    convenio = relationship("Convenio")


class ConvenioTablaSalarial(Base):
    __tablename__ = "convenio_tablas_salariales"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias_profesionales.id"), nullable=False)
    anio = Column(Integer, nullable=False)
    salario_convenio_anual = Column(Numeric(10, 2), nullable=False)
    salario_convenio_mensual = Column(Numeric(10, 2), nullable=False)  # con nº pagas del convenio
    base_calculo_complementos_mensual = Column(Numeric(10, 2), nullable=True)  # art. 37 tipo Metal
    valor_quinquenio_o_trienio = Column(Numeric(10, 2), nullable=True)
    plus_convenio_mensual = Column(Numeric(10, 2), default=0)
    vigente_desde = Column(Date, nullable=False)
    vigente_hasta = Column(Date, nullable=True)

    categoria = relationship("CategoriaProfesional")


class ConvenioDieta(Base):
    """
    Dietas del convenio (compensación de gastos por desplazamiento/manutención,
    NO retribución salarial). Están exentas de cotización y de IRPF hasta los
    límites reglamentarios (art. 9 Reglamento IRPF, RD 439/2007; art. 23 LGSS
    y Orden de cotización) — este MVP las trata como exentas en su totalidad,
    a falta de comprobar que no se superan esos límites reglamentarios.
    """
    __tablename__ = "convenio_dietas"

    id = Column(Integer, primary_key=True, index=True)
    convenio_id = Column(Integer, ForeignKey("convenios.id"), nullable=False)
    anio = Column(Integer, nullable=False)
    media_dieta = Column(Numeric(8, 2), default=0)
    dieta_completa_corta = Column(Numeric(8, 2), default=0)  # viaje < 7 días
    dieta_completa_larga = Column(Numeric(8, 2), default=0)  # viaje >= 7 días
    vigente_desde = Column(Date, nullable=False)
    vigente_hasta = Column(Date, nullable=True)

    convenio = relationship("Convenio")
