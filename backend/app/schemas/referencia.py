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


class CosteCategoriaOut(BaseModel):
    anio: int
    mes: int
    dias_naturales_mes: int
    dias_laborables_mes: int
    horas_mes: Decimal
    convenio_nombre: str
    categoria_grupo: str
    categoria_nombre: str
    salario_base_mensual: Decimal
    prorrata_pagas_extra_mensual: Decimal
    total_devengado_mensual: Decimal
    cuota_empresa_ss_mensual: Decimal
    coste_empresa_mensual: Decimal
    coste_empresa_por_hora: Decimal


class CostePlantillaOut(BaseModel):
    anio: int
    mes: int
    dias_naturales_mes: int
    dias_laborables_mes: int
    horas_mes: Decimal
    convenio_nombre: str
    categoria_grupo: str
    categoria_nombre: str
    numero_empleados: int
    precio_hora_real: Decimal
    salario_base_mensual_individual: Decimal
    prorrata_pagas_extra_individual: Decimal
    horas_extra_total: Decimal
    horas_extra_individual: Decimal
    importe_horas_extra_individual: Decimal
    total_devengado_individual: Decimal
    cuota_empresa_ss_individual: Decimal
    coste_laboral_individual: Decimal
    gastos_reparto_total: Decimal
    gastos_reparto_individual: Decimal
    coste_real_individual: Decimal
    coste_total_plantilla: Decimal
