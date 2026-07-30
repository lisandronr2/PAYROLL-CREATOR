"""
Endpoints de solo lectura para que cualquier usuario autenticado (no solo
admin) pueda consultar de un vistazo los parámetros que el motor aplica al
calcular una nómina: parámetros legales vigentes (SMI, topes de cotización,
recargos de horas extra/nocturnidad, tipos de cotización) y las dietas del
convenio elegido. No permite editar nada — para eso está el panel de admin.
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.models.convenio import ConvenioDieta
from app.models.parametro_legal import ParametroLegal
from app.schemas.parametro_legal import ParametroLegalOut
from app.schemas.referencia import ConvenioDietaOut

router = APIRouter(prefix="/referencia", tags=["referencia"], dependencies=[Depends(get_current_usuario)])


@router.get("/parametros-legales", response_model=list[ParametroLegalOut])
def parametros_legales_vigentes(db: Session = Depends(get_db)):
    hoy = date.today()
    return (
        db.query(ParametroLegal)
        .filter(ParametroLegal.vigente_desde <= hoy)
        .filter((ParametroLegal.vigente_hasta.is_(None)) | (ParametroLegal.vigente_hasta >= hoy))
        .order_by(ParametroLegal.clave, ParametroLegal.grupo_cotizacion)
        .all()
    )


@router.get("/convenios/{convenio_id}/dietas", response_model=list[ConvenioDietaOut])
def dietas_convenio(convenio_id: int, db: Session = Depends(get_db)):
    hoy = date.today()
    return (
        db.query(ConvenioDieta)
        .filter(ConvenioDieta.convenio_id == convenio_id)
        .filter(ConvenioDieta.vigente_desde <= hoy)
        .filter((ConvenioDieta.vigente_hasta.is_(None)) | (ConvenioDieta.vigente_hasta >= hoy))
        .order_by(ConvenioDieta.vigente_desde.desc())
        .all()
    )
