from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import hash_password, require_admin
from app.database import get_db
from app.models.convenio import CategoriaProfesional, Convenio, ConvenioTablaSalarial
from app.models.parametro_legal import ParametroLegal
from app.models.parametro_negocio import ParametroNegocio
from app.models.tabla_irpf import TablaIRPF
from app.models.usuario import Usuario
from app.schemas.convenio import (
    CategoriaProfesionalCreate,
    CategoriaProfesionalOut,
    ConvenioCreate,
    ConvenioOut,
    ConvenioTablaSalarialCreate,
    ConvenioTablaSalarialOut,
    ConvenioUpdate,
)
from app.schemas.parametro_legal import (
    ParametroLegalCreate,
    ParametroLegalOut,
    ParametroLegalUpdate,
    TablaIRPFCreate,
    TablaIRPFOut,
    TablaIRPFUpdate,
)
from app.schemas.parametro_negocio import ParametroNegocioOut, ParametroNegocioUpdate
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------- Usuarios ----------
@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).order_by(Usuario.email).all()


@router.post("/usuarios", response_model=UsuarioOut, status_code=201)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    if payload.rol not in ("admin", "operador"):
        raise HTTPException(status_code=422, detail="Rol inválido (admin u operador)")
    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")
    usuario = Usuario(
        email=payload.email,
        nombre=payload.nombre,
        password_hash=hash_password(payload.password),
        rol=payload.rol,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(usuario_id: int, payload: UsuarioUpdate, db: Session = Depends(get_db)):
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    datos = payload.model_dump(exclude_unset=True)
    if "password" in datos:
        password = datos.pop("password")
        if password:
            usuario.password_hash = hash_password(password)
    if "rol" in datos and datos["rol"] not in ("admin", "operador"):
        raise HTTPException(status_code=422, detail="Rol inválido (admin u operador)")
    for campo, valor in datos.items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


# ---------- Parámetros legales ----------
@router.get("/parametros-legales", response_model=list[ParametroLegalOut])
def listar_parametros_legales(clave: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ParametroLegal)
    if clave:
        query = query.filter(ParametroLegal.clave == clave)
    return query.order_by(ParametroLegal.clave, ParametroLegal.vigente_desde.desc()).all()


@router.post("/parametros-legales", response_model=ParametroLegalOut, status_code=201)
def crear_parametro_legal(payload: ParametroLegalCreate, db: Session = Depends(get_db)):
    parametro = ParametroLegal(**payload.model_dump())
    db.add(parametro)
    db.commit()
    db.refresh(parametro)
    return parametro


@router.patch("/parametros-legales/{parametro_id}", response_model=ParametroLegalOut)
def actualizar_parametro_legal(parametro_id: int, payload: ParametroLegalUpdate, db: Session = Depends(get_db)):
    parametro = db.get(ParametroLegal, parametro_id)
    if not parametro:
        raise HTTPException(status_code=404, detail="Parámetro no encontrado")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(parametro, campo, valor)
    db.commit()
    db.refresh(parametro)
    return parametro


@router.delete("/parametros-legales/{parametro_id}", status_code=204)
def eliminar_parametro_legal(parametro_id: int, db: Session = Depends(get_db)):
    parametro = db.get(ParametroLegal, parametro_id)
    if not parametro:
        raise HTTPException(status_code=404, detail="Parámetro no encontrado")
    db.delete(parametro)
    db.commit()


# ---------- Parámetros de negocio (margen, gastos generales, IVA por defecto) ----------
@router.get("/parametros-negocio", response_model=list[ParametroNegocioOut])
def listar_parametros_negocio(db: Session = Depends(get_db)):
    return db.query(ParametroNegocio).order_by(ParametroNegocio.clave).all()


@router.patch("/parametros-negocio/{parametro_id}", response_model=ParametroNegocioOut)
def actualizar_parametro_negocio(parametro_id: int, payload: ParametroNegocioUpdate, db: Session = Depends(get_db)):
    parametro = db.get(ParametroNegocio, parametro_id)
    if not parametro:
        raise HTTPException(status_code=404, detail="Parámetro no encontrado")
    parametro.valor = payload.valor
    db.commit()
    db.refresh(parametro)
    return parametro


# ---------- Tabla IRPF ----------
@router.get("/tabla-irpf", response_model=list[TablaIRPFOut])
def listar_tabla_irpf(anio: int | None = None, db: Session = Depends(get_db)):
    query = db.query(TablaIRPF)
    if anio:
        query = query.filter(TablaIRPF.anio == anio)
    return query.order_by(TablaIRPF.anio.desc(), TablaIRPF.base_desde_anual).all()


@router.post("/tabla-irpf", response_model=TablaIRPFOut, status_code=201)
def crear_tramo_irpf(payload: TablaIRPFCreate, db: Session = Depends(get_db)):
    tramo = TablaIRPF(**payload.model_dump())
    db.add(tramo)
    db.commit()
    db.refresh(tramo)
    return tramo


@router.patch("/tabla-irpf/{tramo_id}", response_model=TablaIRPFOut)
def actualizar_tramo_irpf(tramo_id: int, payload: TablaIRPFUpdate, db: Session = Depends(get_db)):
    tramo = db.get(TablaIRPF, tramo_id)
    if not tramo:
        raise HTTPException(status_code=404, detail="Tramo no encontrado")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(tramo, campo, valor)
    db.commit()
    db.refresh(tramo)
    return tramo


@router.delete("/tabla-irpf/{tramo_id}", status_code=204)
def eliminar_tramo_irpf(tramo_id: int, db: Session = Depends(get_db)):
    tramo = db.get(TablaIRPF, tramo_id)
    if not tramo:
        raise HTTPException(status_code=404, detail="Tramo no encontrado")
    db.delete(tramo)
    db.commit()


# ---------- Convenios / categorías / tablas salariales ----------
@router.post("/convenios", response_model=ConvenioOut, status_code=201)
def crear_convenio(payload: ConvenioCreate, db: Session = Depends(get_db)):
    convenio = Convenio(**payload.model_dump())
    db.add(convenio)
    db.commit()
    db.refresh(convenio)
    return convenio


@router.patch("/convenios/{convenio_id}", response_model=ConvenioOut)
def actualizar_convenio(convenio_id: int, payload: ConvenioUpdate, db: Session = Depends(get_db)):
    convenio = db.get(Convenio, convenio_id)
    if not convenio:
        raise HTTPException(status_code=404, detail="Convenio no encontrado")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(convenio, campo, valor)
    db.commit()
    db.refresh(convenio)
    return convenio


@router.post("/categorias-profesionales", response_model=CategoriaProfesionalOut, status_code=201)
def crear_categoria(payload: CategoriaProfesionalCreate, db: Session = Depends(get_db)):
    categoria = CategoriaProfesional(**payload.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.post("/tablas-salariales", response_model=ConvenioTablaSalarialOut, status_code=201)
def crear_tabla_salarial(payload: ConvenioTablaSalarialCreate, db: Session = Depends(get_db)):
    tabla = ConvenioTablaSalarial(**payload.model_dump())
    db.add(tabla)
    db.commit()
    db.refresh(tabla)
    return tabla
