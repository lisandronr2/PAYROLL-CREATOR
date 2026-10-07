from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class CalcularLiquidacionRequest(BaseModel):
    contrato_id: int
    # Si no se indica, se usa la fecha de antigüedad (o de inicio) del contrato.
    fecha_ingreso: Optional[date] = None
    fecha_baja: date  # último día de la relación laboral
    motivo: str
    vacaciones_disfrutadas: Decimal = Decimal("0")
    unidad_vacaciones: str = "naturales"  # laborables | naturales
    vacaciones_pendientes_anteriores: Decimal = Decimal("0")
    # Si no se indica, se usa el preaviso que corresponde al motivo y al convenio.
    dias_preaviso_exigidos: Optional[int] = None
    dias_preaviso_trabajados: int = 0
    otras_cantidades: Decimal = Decimal("0")
    indemnizacion_pactada: Decimal = Decimal("0")
    descuentos: Decimal = Decimal("0")


class LineaLiquidacionOut(BaseModel):
    bloque: str
    concepto: str
    importe: Decimal
    detalle: Optional[str] = None
    referencia_legal: Optional[str] = None
    cotiza: bool
    tributa: bool


class LiquidacionOut(BaseModel):
    trabajador_nombre: str
    trabajador_nif: str
    convenio_nombre: str
    categoria: str
    motivo: str
    motivo_texto: str
    fecha_ingreso: date
    fecha_baja: date
    antiguedad_texto: str
    dias_preaviso_exigidos: int
    dias_preaviso_trabajados: int
    vacaciones_dias_naturales: int
    vacaciones_dias_laborables: Optional[int] = None
    salario_diario_indemnizacion: Decimal
    salario_diario_preaviso: Decimal
    lineas: list[LineaLiquidacionOut]
    total_ingresos: Decimal
    indemnizacion_legal: Decimal
    indemnizacion_exenta: Decimal
    base_cotizacion: Decimal
    base_irpf: Decimal
    cotizacion_trabajador: Decimal
    tipo_irpf_pct: Decimal
    retencion_irpf: Decimal
    total_descuentos: Decimal
    total_deducciones: Decimal
    liquido_a_percibir: Decimal
    cuota_empresa_ss: Decimal
    coste_empresa_total: Decimal
    avisos: list[str]


class SugerenciasLiquidacionOut(BaseModel):
    fecha_ingreso: date
    tipo_contrato: str
    categoria: str
    convenio_nombre: str
    dias_preaviso_exigidos: int
    texto_preaviso: str
    vacaciones_dias_naturales: int
    vacaciones_dias_laborables: Optional[int] = None
    unidad_vacaciones_defecto: str
    texto_vacaciones: str
