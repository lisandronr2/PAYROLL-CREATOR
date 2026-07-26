from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ParametroLegalCreate(BaseModel):
    clave: str
    valor: Decimal
    grupo_cotizacion: Optional[int] = None
    vigente_desde: date
    vigente_hasta: Optional[date] = None
    referencia_legal: Optional[str] = None


class ParametroLegalUpdate(BaseModel):
    valor: Optional[Decimal] = None
    vigente_desde: Optional[date] = None
    vigente_hasta: Optional[date] = None
    referencia_legal: Optional[str] = None


class ParametroLegalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    clave: str
    valor: Decimal
    grupo_cotizacion: Optional[int] = None
    vigente_desde: date
    vigente_hasta: Optional[date] = None
    referencia_legal: Optional[str] = None


class TablaIRPFCreate(BaseModel):
    anio: int
    base_desde_anual: Decimal
    base_hasta_anual: Optional[Decimal] = None
    tipo_aplicable_pct: Decimal
    vigente_desde: date
    vigente_hasta: Optional[date] = None


class TablaIRPFUpdate(BaseModel):
    base_desde_anual: Optional[Decimal] = None
    base_hasta_anual: Optional[Decimal] = None
    tipo_aplicable_pct: Optional[Decimal] = None
    vigente_hasta: Optional[date] = None


class TablaIRPFOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    anio: int
    base_desde_anual: Decimal
    base_hasta_anual: Optional[Decimal] = None
    tipo_aplicable_pct: Decimal
    vigente_desde: date
    vigente_hasta: Optional[date] = None
