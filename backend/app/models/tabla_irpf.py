from sqlalchemy import Column, Integer, Numeric, Date

from app.database import Base


class TablaIRPF(Base):
    """
    Tramos simplificados de retención de IRPF por tramo de base anual,
    versionados por año. Uso orientativo: la retención real depende del
    procedimiento general del art. 82-87 del Reglamento IRPF (situación
    familiar, mínimo personal/familiar, reducciones). Ver docs/LEGAL_DISCLAIMER.md.
    """
    __tablename__ = "tabla_irpf"

    id = Column(Integer, primary_key=True, index=True)
    anio = Column(Integer, nullable=False, index=True)
    base_desde_anual = Column(Numeric(12, 2), nullable=False)
    base_hasta_anual = Column(Numeric(12, 2), nullable=True)  # null = sin límite superior
    tipo_aplicable_pct = Column(Numeric(5, 2), nullable=False)
    cuota_acumulada_hasta_tramo = Column(Numeric(12, 2), nullable=False, default=0)
    vigente_desde = Column(Date, nullable=False)
    vigente_hasta = Column(Date, nullable=True)
