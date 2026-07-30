from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str
    password: str
    rol: str = "operador"  # admin | operador


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nombre: str
    rol: str
    activo: bool
    creado_en: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class SolicitarRecuperacionRequest(BaseModel):
    email: EmailStr


class RestablecerPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)
