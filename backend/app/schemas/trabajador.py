from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TrabajadorBase(BaseModel):
    empresa_id: int
    nombre: str
    apellidos: str
    nif: str
    tipo_documento: str = "DNI"  # DNI | NIE
    numero_afiliacion_ss: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    fecha_alta: date
    fecha_baja: Optional[date] = None
    situacion_familiar: str = "soltero"
    hijos_menores_25: int = 0
    grado_discapacidad: int = 0
    iban: Optional[str] = None
    activo: bool = True


class TrabajadorCreate(TrabajadorBase):
    pass


class TrabajadorUpdate(BaseModel):
    empresa_id: Optional[int] = None
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    nif: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_afiliacion_ss: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    fecha_alta: Optional[date] = None
    fecha_baja: Optional[date] = None
    situacion_familiar: Optional[str] = None
    hijos_menores_25: Optional[int] = None
    grado_discapacidad: Optional[int] = None
    iban: Optional[str] = None
    activo: Optional[bool] = None


class TrabajadorOut(TrabajadorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
