from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConvenioDietaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    convenio_id: int
    anio: int
    media_dieta: Decimal
    dieta_completa_corta: Decimal
    dieta_completa_larga: Decimal
    vigente_desde: date
    vigente_hasta: Optional[date] = None
