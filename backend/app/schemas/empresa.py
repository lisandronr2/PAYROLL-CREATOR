from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmpresaBase(BaseModel):
    razon_social: str
    cif: str
    direccion: Optional[str] = None
    poblacion: Optional[str] = None
    cnae: Optional[str] = None
    codigo_cuenta_cotizacion: Optional[str] = None
    # Tipo de cotización por contingencias profesionales (AT/EP), 100% a
    # cargo de la empresa. Depende del CNAE/epígrafe — verificar en la
    # tarifa de primas vigente (DA 61ª LGSS) el tipo exacto aplicable.
    tipo_at_ep_pct: Decimal = Decimal("1.50")
    convenio_id: Optional[int] = None


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    razon_social: Optional[str] = None
    cif: Optional[str] = None
    direccion: Optional[str] = None
    poblacion: Optional[str] = None
    cnae: Optional[str] = None
    codigo_cuenta_cotizacion: Optional[str] = None
    tipo_at_ep_pct: Optional[Decimal] = None
    convenio_id: Optional[int] = None


class EmpresaOut(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: datetime
