"""Estructuras de datos de entrada/salida del motor de cálculo, independientes de la base de datos.

Mantener el motor puro (sin sesión de BD) permite testearlo con pytest sin
necesidad de una base de datos real.
"""
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ParametrosCotizacion:
    tipo_cc_empresa_pct: Decimal
    tipo_cc_trabajador_pct: Decimal
    tipo_desempleo_empresa_pct: Decimal
    tipo_desempleo_trabajador_pct: Decimal
    tipo_fp_empresa_pct: Decimal
    tipo_fp_trabajador_pct: Decimal
    tipo_fogasa_empresa_pct: Decimal
    tipo_mei_empresa_pct: Decimal
    tipo_mei_trabajador_pct: Decimal
    tope_min_grupo_mensual: Decimal
    tope_max_mensual: Decimal
    smi_mensual: Decimal
    recargo_hora_extra_pct: Decimal
    recargo_hora_extra_nocturna_pct: Decimal
    plus_nocturnidad_pct: Decimal


@dataclass
class DatosConvenioContrato:
    nombre_convenio: str
    numero_pagas: int
    jornada_anual_horas: Decimal
    salario_convenio_mensual: Decimal
    base_calculo_complementos_mensual: Decimal
    valor_quinquenio_o_trienio: Decimal
    plus_convenio_mensual: Decimal
    jornada_porcentaje: Decimal
    tipo_contrato: str
    pagas_extra_prorrateadas: bool
    numero_quinquenios_o_trienios: int
    grupo_cotizacion: int
    salario_pactado_mensual: Decimal | None = None  # sustituye al de convenio si es mejora
    media_dieta: Decimal = Decimal("0")
    dieta_completa_corta: Decimal = Decimal("0")  # viaje < 7 días
    dieta_completa_larga: Decimal = Decimal("0")  # viaje >= 7 días


@dataclass
class EventosMes:
    periodo_anio: int
    periodo_mes: int
    dias_naturales_periodo: int = 30
    dias_trabajados: int | None = None
    horas_extra: Decimal = Decimal("0")
    horas_extra_nocturnas: Decimal = Decimal("0")
    horas_nocturnas_ordinarias: Decimal = Decimal("0")
    dias_it: int = 0
    dias_vacaciones: int = 0
    dias_festivos_trabajados: int = 0
    anticipos: Decimal = Decimal("0")
    embargo_mensual: Decimal = Decimal("0")
    numero_medias_dietas: int = 0
    numero_dietas_completas_cortas: int = 0  # viaje < 7 días
    numero_dietas_completas_largas: int = 0  # viaje >= 7 días


@dataclass
class LineaCalculo:
    bloque: str  # devengo | cotizacion_trabajador | cotizacion_empresa | deduccion
    concepto: str
    importe: Decimal
    base: Decimal | None = None
    tipo_pct: Decimal | None = None
    referencia_legal: str | None = None
    # Solo relevante para líneas de bloque "devengo": si computa en la base
    # de cotización a la Seguridad Social (True) o está exento (False, p.ej.
    # dietas o prestación de IT).
    cotiza: bool = True


@dataclass
class ResultadoNomina:
    lineas: list[LineaCalculo] = field(default_factory=list)
    total_devengado: Decimal = Decimal("0")
    total_deducciones: Decimal = Decimal("0")
    liquido_a_percibir: Decimal = Decimal("0")
    base_cotizacion_comun: Decimal = Decimal("0")
    base_sujeta_irpf: Decimal = Decimal("0")
    coste_empresa_total: Decimal = Decimal("0")
    total_dietas_exentas: Decimal = Decimal("0")
