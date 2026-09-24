from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_usuario, require_admin
from app.database import get_db
from app.models.partida_catalogo import PartidaCatalogo
from app.schemas.partida_catalogo import PartidaCatalogoCreate, PartidaCatalogoOut, PartidaCatalogoUpdate

router = APIRouter(
    prefix="/partidas-catalogo", tags=["partidas-catalogo"], dependencies=[Depends(get_current_usuario)]
)


def _recalcular(partida: PartidaCatalogo) -> None:
    partida.coste_directo = partida.precio_coste_mo + partida.precio_material + partida.precio_medios_aux
    partida.precio_venta = (partida.coste_directo * (1 + partida.margen_pct / Decimal(100))).quantize(Decimal("0.01"))


@router.get("", response_model=list[PartidaCatalogoOut])
def listar_partidas(solo_activas: bool = True, db: Session = Depends(get_db)):
    query = db.query(PartidaCatalogo)
    if solo_activas:
        query = query.filter(PartidaCatalogo.activo.is_(True))
    return query.order_by(PartidaCatalogo.familia, PartidaCatalogo.nombre).all()


@router.post("", response_model=PartidaCatalogoOut, status_code=201, dependencies=[Depends(require_admin)])
def crear_partida(payload: PartidaCatalogoCreate, db: Session = Depends(get_db)):
    partida = PartidaCatalogo(**payload.model_dump())
    _recalcular(partida)
    db.add(partida)
    db.commit()
    db.refresh(partida)
    return partida


@router.patch("/{partida_id}", response_model=PartidaCatalogoOut, dependencies=[Depends(require_admin)])
def actualizar_partida(partida_id: int, payload: PartidaCatalogoUpdate, db: Session = Depends(get_db)):
    partida = db.get(PartidaCatalogo, partida_id)
    if not partida:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(partida, campo, valor)
    _recalcular(partida)
    db.commit()
    db.refresh(partida)
    return partida
