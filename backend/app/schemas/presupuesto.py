from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PresupuestoLineaPersonalCreate(BaseModel):
    categoria_id: int
    cantidad_personas: int = 1
    jornada_porcentaje: Decimal = Decimal("100")
    dias_dedicacion: Decimal
    pagas_extra_prorrateadas: bool = True
    complemento_mensual: Decimal = Decimal("0")
    numero_medias_dietas: int = 0
    numero_dietas_completas_cortas: int = 0
    numero_dietas_completas_largas: int = 0


class PresupuestoLineaOtroCosteCreate(BaseModel):
    concepto: str
    cantidad: Decimal = Decimal("1")
    precio_unitario: Decimal


class PresupuestoCreate(BaseModel):
    empresa_id: int
    convenio_id: int
    nombre: str
    cliente_nombre: Optional[str] = None
    cliente_nif: Optional[str] = None
    fecha: date
    # Si no se indica alguno, se usa el valor por defecto configurado
    # (ver ParametroNegocio) en el momento de crear/actualizar.
    margen_beneficio_pct: Optional[Decimal] = None
    gastos_generales_pct: Optional[Decimal] = None
    iva_pct: Optional[Decimal] = None
    notas: Optional[str] = None
    lineas_personal: list[PresupuestoLineaPersonalCreate] = []
    lineas_otros: list[PresupuestoLineaOtroCosteCreate] = []


class PresupuestoLineaPersonalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    categoria_id: int
    cantidad_personas: int
    jornada_porcentaje: Decimal
    dias_dedicacion: Decimal
    pagas_extra_prorrateadas: bool
    complemento_mensual: Decimal
    numero_medias_dietas: int
    numero_dietas_completas_cortas: int
    numero_dietas_completas_largas: int
    coste_unitario: Decimal
    coste_total_linea: Decimal
    coste_mano_obra_total: Decimal
    coste_dietas_total: Decimal


class PresupuestoLineaOtroCosteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    concepto: str
    cantidad: Decimal
    precio_unitario: Decimal
    importe: Decimal


class PresupuestoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empresa_id: int
    convenio_id: int
    nombre: str
    cliente_nombre: Optional[str] = None
    cliente_nif: Optional[str] = None
    fecha: date
    notas: Optional[str] = None
    margen_beneficio_pct: Decimal
    gastos_generales_pct: Decimal
    iva_pct: Decimal
    coste_directo_mano_obra: Decimal
    coste_directo_dietas: Decimal
    coste_directo_otros: Decimal
    coste_directo_total: Decimal
    gastos_generales_importe: Decimal
    coste_total: Decimal
    margen_importe: Decimal
    precio_venta: Decimal
    iva_importe: Decimal
    precio_total_cliente: Decimal
    lineas_personal: list[PresupuestoLineaPersonalOut] = []
    lineas_otros: list[PresupuestoLineaOtroCosteOut] = []
