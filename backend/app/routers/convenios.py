from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.models.convenio import Convenio, CategoriaProfesional, ConvenioTablaSalarial
from app.schemas.convenio import ConvenioOut, CategoriaProfesionalOut, ConvenioTablaSalarialOut

router = APIRouter(prefix="/convenios", tags=["convenios"], dependencies=[Depends(get_current_usuario)])


@router.get("", response_model=list[ConvenioOut])
def listar_convenios(db: Session = Depends(get_db)):
    return db.query(Convenio).all()


@router.get("/{convenio_id}/categorias", response_model=list[CategoriaProfesionalOut])
def listar_categorias(convenio_id: int, db: Session = Depends(get_db)):
    return db.query(CategoriaProfesional).filter(CategoriaProfesional.convenio_id == convenio_id).all()


@router.get("/categorias/{categoria_id}/tabla-salarial", response_model=list[ConvenioTablaSalarialOut])
def tabla_salarial_categoria(categoria_id: int, db: Session = Depends(get_db)):
    tablas = (
        db.query(ConvenioTablaSalarial)
        .filter(ConvenioTablaSalarial.categoria_id == categoria_id)
        .order_by(ConvenioTablaSalarial.vigente_desde.desc())
        .all()
    )
    if not tablas:
        raise HTTPException(status_code=404, detail="No hay tabla salarial para esta categoría")
    return tablas
