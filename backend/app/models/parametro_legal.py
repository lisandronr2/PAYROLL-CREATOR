from sqlalchemy import Column, Integer, String, Numeric, Date, Text

from app.database import Base


class ParametroLegal(Base):
    """
    Parámetros legales versionados (tipos de cotización, SMI, topes, etc.).
    Editables sin tocar código para que una asesoría los mantenga al día.
    """
    __tablename__ = "parametros_legales"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False, index=True)
    # claves esperadas: smi_mensual, tope_min_cotizacion_grupo_N, tope_max_cotizacion,
    # tipo_cc_empresa, tipo_cc_trabajador, tipo_desempleo_indefinido_empresa,
    # tipo_desempleo_indefinido_trabajador, tipo_desempleo_temporal_empresa,
    # tipo_desempleo_temporal_trabajador, tipo_fp_empresa, tipo_fp_trabajador,
    # tipo_fogasa_empresa, tipo_mei_empresa, tipo_mei_trabajador,
    # recargo_hora_extra_pct, plus_kilometraje
    valor = Column(Numeric(14, 4), nullable=False)
    grupo_cotizacion = Column(Integer, nullable=True)  # solo aplica a topes por grupo
    vigente_desde = Column(Date, nullable=False)
    vigente_hasta = Column(Date, nullable=True)
    referencia_legal = Column(Text)  # p.ej. "Orden PJC/.../2026 cotización SS"
