from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_usuario
from app.database import get_db
from app.models.contrato import Contrato
from app.pdf.extractor_contrato import extraer_datos_contrato
from app.schemas.contrato import ContratoCreate, ContratoOut

router = APIRouter(prefix="/contratos", tags=["contratos"], dependencies=[Depends(get_current_usuario)])


@router.get("", response_model=list[ContratoOut])
def listar_contratos(trabajador_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Contrato)
    if trabajador_id is not None:
        query = query.filter(Contrato.trabajador_id == trabajador_id)
    return query.all()


@router.post("/extraer-pdf")
async def extraer_pdf_contrato(archivo: UploadFile):
    """
    Lee un contrato ya firmado en PDF y sugiere valores para el formulario de
    alta (fecha de inicio, tipo de contrato, jornada, salario, puesto). Es
    heurístico: no garantiza acertar todos los campos y el usuario debe
    revisar el resultado antes de guardar el contrato.
    """
    if archivo.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=422, detail="El archivo debe ser un PDF")

    contenido = await archivo.read()
    try:
        return extraer_datos_contrato(contenido)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"No se pudo leer el PDF: {exc}")


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
