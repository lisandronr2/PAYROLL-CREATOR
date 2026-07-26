from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class GenerarNominaRequest(BaseModel):
    contrato_id: int
    periodo_anio: int
    periodo_mes: int
    tipo: str = "mensual"  # mensual, finiquito

    dias_naturales_periodo: int = 30
    dias_trabajados: Optional[int] = None  # si None, se asume el mes completo menos IT/vacaciones
    horas_extra: Decimal = Decimal("0")
    horas_extra_nocturnas: Decimal = Decimal("0")
    dias_it: int = 0
    dias_vacaciones: int = 0
    horas_nocturnas_ordinarias: Decimal = Decimal("0")
    dias_festivos_trabajados: int = 0
    anticipos: Decimal = Decimal("0")
    embargo_mensual: Decimal = Decimal("0")


class NominaLineaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    bloque: str
    concepto: str
    base: Optional[Decimal] = None
    tipo_pct: Optional[Decimal] = None
    importe: Decimal
    referencia_legal: Optional[str] = None
    orden: int


class NominaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    contrato_id: int
    periodo_anio: int
    periodo_mes: int
    tipo: str
    dias_naturales_periodo: int
    dias_trabajados: int
    total_devengado: Decimal
    total_deducciones: Decimal
    liquido_a_percibir: Decimal
    base_cotizacion_comun: Decimal
    base_sujeta_irpf: Decimal
    coste_empresa_total: Decimal
    lineas: list[NominaLineaOut] = []
