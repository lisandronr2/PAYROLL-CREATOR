from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmpresaBase(BaseModel):
    razon_social: str
    cif: str
    direccion: Optional[str] = None
    cnae: Optional[str] = None
    codigo_cuenta_cotizacion: Optional[str] = None
    convenio_id: Optional[int] = None


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    razon_social: Optional[str] = None
    cif: Optional[str] = None
    direccion: Optional[str] = None
    cnae: Optional[str] = None
    codigo_cuenta_cotizacion: Optional[str] = None
    convenio_id: Optional[int] = None


class EmpresaOut(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: datetime
