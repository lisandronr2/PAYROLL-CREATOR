from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.models.contrato import Contrato
from app.schemas.contrato import ContratoCreate, ContratoOut

router = APIRouter(prefix="/contratos", tags=["contratos"], dependencies=[Depends(get_current_usuario)])


@router.get("", response_model=list[ContratoOut])
def listar_contratos(trabajador_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Contrato)
    if trabajador_id is not None:
        query = query.filter(Contrato.trabajador_id == trabajador_id)
    return query.all()


@router.post("", response_model=ContratoOut, status_code=201)
def crear_contrato(payload: ContratoCreate, db: Session = Depends(get_db)):
    contrato = Contrato(**payload.model_dump())
    db.add(contrato)
    db.commit()
    db.refresh(contrato)
    return contrato


@router.get("/{contrato_id}", response_model=ContratoOut)
def obtener_contrato(contrato_id: int, db: Session = Depends(get_db)):
    contrato = db.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato
