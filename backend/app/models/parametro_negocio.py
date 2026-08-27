from sqlalchemy import Column, Integer, String, Numeric

from app.database import Base


class ParametroNegocio(Base):
    """
    Parámetros de NEGOCIO (no legales): márgenes y porcentajes que decide la
    propia empresa y que no se pueden derivar de ninguna ley ni convenio.
    Se usan como valor por defecto al crear un presupuesto, pero cada
    presupuesto puede sobrescribirlos si ese proyecto lo requiere.
    """
    __tablename__ = "parametros_negocio"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False, unique=True, index=True)
    # claves esperadas: margen_beneficio_pct_defecto, gastos_generales_pct_defecto, iva_pct_defecto
    valor = Column(Numeric(6, 3), nullable=False)
    descripcion = Column(String, nullable=True)
