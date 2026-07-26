from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConvenioCreate(BaseModel):
    nombre: str
    ambito: Optional[str] = None
    provincia: Optional[str] = None
    codigo_convenio: Optional[str] = None
    fuente: Optional[str] = None
    numero_pagas: int = 14
    jornada_anual_horas: Decimal = Decimal("1800")
    notas: Optional[str] = None


class ConvenioUpdate(BaseModel):
    nombre: Optional[str] = None
    ambito: Optional[str] = None
    provincia: Optional[str] = None
    codigo_convenio: Optional[str] = None
    fuente: Optional[str] = None
    numero_pagas: Optional[int] = None
    jornada_anual_horas: Optional[Decimal] = None
    notas: Optional[str] = None


class CategoriaProfesionalCreate(BaseModel):
    convenio_id: int
    grupo: str
    nombre: str
    grupo_cotizacion: int


class ConvenioTablaSalarialCreate(BaseModel):
    categoria_id: int
    anio: int
    salario_convenio_anual: Decimal
    salario_convenio_mensual: Decimal
    base_calculo_complementos_mensual: Optional[Decimal] = None
    valor_quinquenio_o_trienio: Optional[Decimal] = None
    plus_convenio_mensual: Decimal = Decimal("0")
    vigente_desde: date
    vigente_hasta: Optional[date] = None


class ConvenioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    ambito: Optional[str] = None
    provincia: Optional[str] = None
    codigo_convenio: Optional[str] = None
    fuente: Optional[str] = None
    numero_pagas: int
    jornada_anual_horas: Decimal
    notas: Optional[str] = None


class CategoriaProfesionalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    convenio_id: int
    grupo: str
    nombre: str
    grupo_cotizacion: int


class ConvenioTablaSalarialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    categoria_id: int
    anio: int
    salario_convenio_anual: Decimal
    salario_convenio_mensual: Decimal
    base_calculo_complementos_mensual: Optional[Decimal] = None
    valor_quinquenio_o_trienio: Optional[Decimal] = None
    plus_convenio_mensual: Decimal
    vigente_desde: date
    vigente_hasta: Optional[date] = None
