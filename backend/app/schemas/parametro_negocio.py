from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ParametroNegocioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    clave: str
    valor: Decimal
    descripcion: Optional[str] = None


class ParametroNegocioUpdate(BaseModel):
    valor: Decimal
