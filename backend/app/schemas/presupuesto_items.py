from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PresupuestoItemsLineaCreate(BaseModel):
    partida_id: int
    cantidad: Decimal = Decimal("1")
    descuento_pct: Decimal = Decimal("0")


class PresupuestoItemsCreate(BaseModel):
    empresa_id: int
    nombre: str
    cliente_nombre: Optional[str] = None
    cliente_nif: Optional[str] = None
    fecha: date
    notas: Optional[str] = None
    # Si no se indica, se usa el valor por defecto configurado (ver ParametroNegocio).
    iva_pct: Optional[Decimal] = None
    lineas: list[PresupuestoItemsLineaCreate] = []


class PresupuestoItemsLineaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    partida_id: Optional[int] = None
    familia: str
    nombre: str
    unidad: str
    coste_directo_unitario: Decimal
    margen_pct: Decimal
    precio_unitario: Decimal
    cantidad: Decimal
    descuento_pct: Decimal
    importe: Decimal


class PresupuestoItemsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empresa_id: int
    nombre: str
    cliente_nombre: Optional[str] = None
    cliente_nif: Optional[str] = None
    fecha: date
    notas: Optional[str] = None
    iva_pct: Decimal
    subtotal: Decimal
    iva_importe: Decimal
    precio_total_cliente: Decimal
    lineas: list[PresupuestoItemsLineaOut] = []
