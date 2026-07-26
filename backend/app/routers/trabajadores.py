from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.models.trabajador import Trabajador
from app.schemas.trabajador import TrabajadorCreate, TrabajadorOut, TrabajadorUpdate

router = APIRouter(prefix="/trabajadores", tags=["trabajadores"], dependencies=[Depends(get_current_usuario)])


@router.get("", response_model=list[TrabajadorOut])
def listar_trabajadores(empresa_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Trabajador)
    if empresa_id is not None:
        query = query.filter(Trabajador.empresa_id == empresa_id)
    return query.order_by(Trabajador.apellidos).all()


@router.post("", response_model=TrabajadorOut, status_code=201)
def crear_trabajador(payload: TrabajadorCreate, db: Session = Depends(get_db)):
    if db.query(Trabajador).filter(Trabajador.nif == payload.nif).first():
        raise HTTPException(status_code=409, detail="Ya existe un trabajador con ese NIF")
    trabajador = Trabajador(**payload.model_dump())
    db.add(trabajador)
    db.commit()
    db.refresh(trabajador)
    return trabajador


@router.get("/{trabajador_id}", response_model=TrabajadorOut)
def obtener_trabajador(trabajador_id: int, db: Session = Depends(get_db)):
    trabajador = db.get(Trabajador, trabajador_id)
    if not trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    return trabajador


@router.patch("/{trabajador_id}", response_model=TrabajadorOut)
def actualizar_trabajador(trabajador_id: int, payload: TrabajadorUpdate, db: Session = Depends(get_db)):
    trabajador = db.get(Trabajador, trabajador_id)
    if not trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(trabajador, campo, valor)
    db.commit()
    db.refresh(trabajador)
    return trabajador
