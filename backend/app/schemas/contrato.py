from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContratoBase(BaseModel):
    trabajador_id: int
    convenio_id: int
    categoria_id: int
    tipo_contrato: str
    jornada_porcentaje: Decimal = Decimal("100")
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    salario_pactado_mensual: Optional[Decimal] = None
    pagas_extra_prorrateadas: bool = False
    fecha_antiguedad: Optional[date] = None


class ContratoCreate(ContratoBase):
    pass


class ContratoOut(ContratoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
