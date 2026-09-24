from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PartidaCatalogoCreate(BaseModel):
    familia: str
    nombre: str
    unidad: str
    precio_coste_mo: Decimal = Decimal("0")
    precio_material: Decimal = Decimal("0")
    precio_medios_aux: Decimal = Decimal("0")
    margen_pct: Decimal = Decimal("20")
    observaciones: Optional[str] = None
    activo: bool = True


class PartidaCatalogoUpdate(BaseModel):
    familia: Optional[str] = None
    nombre: Optional[str] = None
    unidad: Optional[str] = None
    precio_coste_mo: Optional[Decimal] = None
    precio_material: Optional[Decimal] = None
    precio_medios_aux: Optional[Decimal] = None
    margen_pct: Optional[Decimal] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None


class PartidaCatalogoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    familia: str
    nombre: str
    unidad: str
    precio_coste_mo: Decimal
    precio_material: Decimal
    precio_medios_aux: Decimal
    coste_directo: Decimal
    margen_pct: Decimal
    precio_venta: Decimal
    observaciones: Optional[str] = None
    activo: bool
