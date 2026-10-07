"""
Numeración de presupuestos: un número correlativo por año y por tipo de
presupuesto. Al crear se propone el MENOR número libre del año, de modo que
el número de un presupuesto borrado se recupera para el siguiente. El usuario
puede cambiarlo a mano; no se permite repetir un número dentro del mismo año.
"""
from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session


def _numeros_usados(db: Session, modelo, anio: int, excluir_id: Optional[int]) -> set[int]:
    consulta = db.query(modelo.numero).filter(
        modelo.fecha >= date(anio, 1, 1), modelo.fecha <= date(anio, 12, 31), modelo.numero.isnot(None)
    )
    if excluir_id is not None:
        consulta = consulta.filter(modelo.id != excluir_id)
    return {fila[0] for fila in consulta.all()}


def siguiente_numero(db: Session, modelo, anio: int, excluir_id: Optional[int] = None) -> int:
    usados = _numeros_usados(db, modelo, anio, excluir_id)
    numero = 1
    while numero in usados:
        numero += 1
    return numero


def asignar_numero(db: Session, modelo, presupuesto, solicitado: Optional[int], fecha: date) -> None:
    """Fija `presupuesto.numero`: el pedido por el usuario (validado) o, si no
    se indica, el que ya tenía (si sigue libre en ese año) o el menor libre."""
    usados = _numeros_usados(db, modelo, fecha.year, presupuesto.id)
    if solicitado is not None:
        if solicitado < 1:
            raise HTTPException(status_code=422, detail="El número de presupuesto debe ser 1 o mayor")
        if solicitado in usados:
            raise HTTPException(
                status_code=409, detail=f"El número {solicitado} ya está usado por otro presupuesto de {fecha.year}"
            )
        presupuesto.numero = solicitado
    elif presupuesto.numero is None or presupuesto.numero in usados:
        presupuesto.numero = siguiente_numero(db, modelo, fecha.year, presupuesto.id)


def numero_visible(presupuesto, prefijo: str = "") -> str:
    """'2026-0007' (o '2026-I0007'). Si aún no tiene número guardado, usa el id."""
    numero = presupuesto.numero if presupuesto.numero is not None else presupuesto.id
    return f"{presupuesto.fecha.year}-{prefijo}{numero:04d}"


def rellenar_numeros_pendientes(db: Session, modelo) -> None:
    """Presupuestos anteriores a esta función: conservan como número su id
    (el que ya figuraba en sus PDF), salvo que ya esté cogido en su año."""
    pendientes = db.query(modelo).filter(modelo.numero.is_(None)).order_by(modelo.id).all()
    for p in pendientes:
        usados = _numeros_usados(db, modelo, p.fecha.year, p.id)
        p.numero = p.id if p.id not in usados else siguiente_numero(db, modelo, p.fecha.year, p.id)
        db.flush()
    db.commit()
