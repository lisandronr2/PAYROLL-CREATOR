"""
Liquidación (finiquito) por fin de contrato.

Conceptos que calcula, con su base legal:
  - Salario de los días trabajados del mes de la baja (art. 29 ET).
  - Parte proporcional de pagas extraordinarias devengadas y no abonadas
    (art. 31 ET), según el devengo del convenio.
  - Vacaciones devengadas y no disfrutadas (art. 38 ET y convenio); si se
    disfrutaron de más, se descuentan.
  - Preaviso: el trabajador que dimite sin preaviso sufre un descuento
    (art. 49.1.d ET y convenio); la empresa que no lo concede en el despido
    objetivo (art. 53.1.c ET) o en el fin de un temporal de más de un año
    (art. 49.1.c ET) abona los días omitidos.
  - Indemnización por extinción: despido improcedente (33 días/año, máx. 24
    mensualidades; 45 días/año por el tiempo anterior al 12/02/2012, art. 56
    ET y DT 11ª Ley 3/2012), despido objetivo (20 días/año, máx. 12
    mensualidades, art. 53 ET) y fin de contrato temporal (12 días/año,
    art. 49.1.c ET).
  - Cotización a la Seguridad Social, retención de IRPF y coste para la
    empresa. La indemnización legal por despido está exenta de IRPF hasta
    180.000 € (art. 7.e LIRPF) y de cotización (art. 147.2.c LGSS); la
    compensación por preaviso omitido NO está exenta: desde el criterio de la
    TGSS publicado en el boletín RED 08/2026 cotiza como salario.

⚠️ Es un cálculo orientativo: no sustituye a un asesor laboral (ver
docs/LEGAL_DISCLAIMER.md). Simplificaciones principales: no se promedian los
conceptos variables de los 3 últimos meses para las vacaciones; las
fracciones de mes se prorratean por días; la retención de IRPF aplica el tipo
de una nómina ordinaria; la reducción del 30 % de rentas irregulares no se
modela; y se supone que ya se pagaron las nóminas de los meses anteriores.
"""
import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.engine.calculo import calcular_devengos, calcular_irpf
from app.engine.tipos import DatosConvenioContrato, EventosMes, ParametrosCotizacion

TWO = Decimal("0.01")

FECHA_REFORMA_2012 = date(2012, 2, 12)
LIMITE_EXENCION_IRPF_INDEMNIZACION = Decimal("180000")  # art. 7.e LIRPF
DIAS_NATURALES_VACACIONES_MINIMO = 30  # art. 38 ET

MOTIVOS = {
    "dimision": "Dimisión (baja voluntaria)",
    "despido_disciplinario": "Despido disciplinario procedente",
    "despido_improcedente": "Despido improcedente",
    "despido_objetivo": "Despido objetivo (causas económicas, técnicas, organizativas o de producción)",
    "fin_contrato_temporal": "Fin de contrato temporal",
    "mutuo_acuerdo": "Mutuo acuerdo",
    "fin_periodo_prueba": "Fin del periodo de prueba",
}

UNIDADES_VACACIONES = ("laborables", "naturales")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(TWO, rounding=ROUND_HALF_UP)


@dataclass
class LineaLiquidacion:
    # devengo | indemnizacion | descuento | deduccion
    bloque: str
    concepto: str
    importe: Decimal  # siempre positivo; el bloque indica si suma o resta
    detalle: str | None = None
    referencia_legal: str | None = None
    cotiza: bool = False
    tributa: bool = False


@dataclass
class EntradaLiquidacion:
    convenio: DatosConvenioContrato
    parametros: ParametrosCotizacion
    tramos_irpf: list[tuple[Decimal, Decimal | None, Decimal]]
    fecha_ingreso: date
    fecha_baja: date  # último día de la relación laboral
    motivo: str
    dias_preaviso_exigidos: int = 0
    dias_preaviso_trabajados: int = 0  # días de preaviso efectivamente cumplidos (trabajados)
    vacaciones_dias_naturales: int = DIAS_NATURALES_VACACIONES_MINIMO
    vacaciones_dias_laborables: int | None = None
    vacaciones_disfrutadas: Decimal = Decimal("0")
    unidad_vacaciones: str = "naturales"
    vacaciones_pendientes_anteriores: Decimal = Decimal("0")
    otras_cantidades: Decimal = Decimal("0")
    indemnizacion_pactada: Decimal = Decimal("0")
    descuentos: Decimal = Decimal("0")
    hijos_menores_25: int = 0
    grado_discapacidad: int = 0
    edad: int | None = None


@dataclass
class ResultadoLiquidacion:
    lineas: list[LineaLiquidacion] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    antiguedad_texto: str = ""
    salario_diario_indemnizacion: Decimal = Decimal("0")
    salario_diario_preaviso: Decimal = Decimal("0")
    total_ingresos: Decimal = Decimal("0")  # devengos + indemnizaciones (bruto)
    indemnizacion_legal: Decimal = Decimal("0")
    indemnizacion_exenta: Decimal = Decimal("0")
    base_cotizacion: Decimal = Decimal("0")
    base_irpf: Decimal = Decimal("0")
    cotizacion_trabajador: Decimal = Decimal("0")
    tipo_irpf_pct: Decimal = Decimal("0")
    retencion_irpf: Decimal = Decimal("0")
    total_descuentos: Decimal = Decimal("0")
    total_deducciones: Decimal = Decimal("0")
    liquido_a_percibir: Decimal = Decimal("0")
    cuota_empresa_ss: Decimal = Decimal("0")
    coste_empresa_total: Decimal = Decimal("0")


# ---------- antigüedad ----------

def _sumar_meses(fecha: date, meses: int) -> date:
    total = fecha.month - 1 + meses
    anio = fecha.year + total // 12
    mes = total % 12 + 1
    return date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def diferencia_meses_dias(desde: date, hasta_exclusivo: date) -> tuple[int, int]:
    """Meses completos y días sobrantes entre dos fechas (la final excluida)."""
    if hasta_exclusivo <= desde:
        return 0, 0
    meses = (hasta_exclusivo.year - desde.year) * 12 + hasta_exclusivo.month - desde.month
    if hasta_exclusivo.day < desde.day:
        meses -= 1
    dias = (hasta_exclusivo - _sumar_meses(desde, meses)).days
    return meses, dias


def anios_de_servicio(desde: date, hasta_exclusivo: date) -> Decimal:
    """Años de servicio con los periodos inferiores a un año prorrateados por
    meses (art. 56.1 ET); los días sobrantes se prorratean sobre 30 días."""
    meses, dias = diferencia_meses_dias(desde, hasta_exclusivo)
    return Decimal(meses) / Decimal(12) + Decimal(dias) / Decimal(360)


def texto_antiguedad(desde: date, hasta_exclusivo: date) -> str:
    meses, dias = diferencia_meses_dias(desde, hasta_exclusivo)
    anios, meses_sueltos = divmod(meses, 12)
    return f"{anios} años, {meses_sueltos} meses y {dias} días"


# ---------- indemnización ----------

@dataclass
class Indemnizacion:
    importe: Decimal
    dias: Decimal
    detalle: str
    referencia_legal: str


def calcular_indemnizacion(
    motivo: str, fecha_ingreso: date, fecha_baja: date, salario_diario: Decimal
) -> Indemnizacion | None:
    fin = fecha_baja + timedelta(days=1)

    if motivo == "despido_improcedente":
        anios_pre = (
            anios_de_servicio(fecha_ingreso, min(fin, FECHA_REFORMA_2012))
            if fecha_ingreso < FECHA_REFORMA_2012
            else Decimal("0")
        )
        anios_post = (
            anios_de_servicio(max(fecha_ingreso, FECHA_REFORMA_2012), fin)
            if fin > FECHA_REFORMA_2012
            else Decimal("0")
        )
        dias_pre = Decimal(45) * anios_pre
        dias_post = Decimal(33) * anios_post
        dias_totales = dias_pre + dias_post

        tope = Decimal(720)  # 24 mensualidades
        if dias_pre > tope:
            tope = min(dias_pre, Decimal(1260))  # DT 11ª Ley 3/2012: hasta 42 mensualidades
        dias = min(dias_totales, tope)
        detalle = f"33 días/año × {anios_post:.2f} años desde el 12/02/2012"
        if anios_pre:
            detalle = f"45 días/año × {anios_pre:.2f} años hasta el 11/02/2012 + " + detalle
        if dias < dias_totales:
            detalle += f" — limitado a {dias:.2f} días (tope legal)"
        return Indemnizacion(
            importe=_q(dias * salario_diario),
            dias=dias,
            detalle=f"{dias:.2f} días de salario ({detalle})",
            referencia_legal="Art. 56 ET y DT 11ª Ley 3/2012",
        )

    if motivo == "despido_objetivo":
        anios = anios_de_servicio(fecha_ingreso, fin)
        dias_totales = Decimal(20) * anios
        dias = min(dias_totales, Decimal(360))  # 12 mensualidades
        detalle = f"20 días/año × {anios:.2f} años"
        if dias < dias_totales:
            detalle += " — limitado a 12 mensualidades"
        return Indemnizacion(
            importe=_q(dias * salario_diario),
            dias=dias,
            detalle=f"{dias:.2f} días de salario ({detalle})",
            referencia_legal="Art. 53.1.b ET",
        )

    if motivo == "fin_contrato_temporal":
        anios = anios_de_servicio(fecha_ingreso, fin)
        dias = Decimal(12) * anios
        return Indemnizacion(
            importe=_q(dias * salario_diario),
            dias=dias,
            detalle=f"{dias:.2f} días de salario (12 días/año × {anios:.2f} años)",
            referencia_legal="Art. 49.1.c ET",
        )

    return None


# ---------- vacaciones ----------

def calcular_vacaciones(
    fecha_ingreso: date,
    fecha_baja: date,
    dias_naturales_anuales: int,
    dias_laborables_anuales: int | None,
    disfrutadas: Decimal,
    unidad: str,
    pendientes_anteriores: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Devuelve (devengadas, disfrutadas, de años anteriores, pendientes), todo
    en días naturales. Las vacaciones se devengan por días de servicio del año
    de la baja; si el convenio las expresa en laborables, los días disfrutados
    se convierten a naturales con la equivalencia del convenio."""
    if unidad not in UNIDADES_VACACIONES:
        raise ValueError("La unidad de las vacaciones debe ser 'laborables' o 'naturales'")
    if unidad == "laborables" and not dias_laborables_anuales:
        raise ValueError("El convenio no define vacaciones en días laborables: usa días naturales")

    inicio = max(date(fecha_baja.year, 1, 1), fecha_ingreso)
    dias_servicio = (fecha_baja - inicio).days + 1
    dias_anio = 366 if calendar.isleap(fecha_baja.year) else 365
    devengadas = _q(Decimal(dias_naturales_anuales) * Decimal(dias_servicio) / Decimal(dias_anio))

    factor = (
        Decimal(dias_naturales_anuales) / Decimal(dias_laborables_anuales)
        if unidad == "laborables"
        else Decimal(1)
    )
    disfrutadas_nat = _q(disfrutadas * factor)
    anteriores_nat = _q(pendientes_anteriores * factor)
    pendientes = _q(devengadas + anteriores_nat - disfrutadas_nat)
    return devengadas, disfrutadas_nat, anteriores_nat, pendientes


# ---------- pagas extraordinarias ----------

def pagas_extra_pendientes(
    fecha_ingreso: date,
    fecha_baja: date,
    numero_pagas: int,
    base_paga_mensual: Decimal,
    prorrateadas: bool,
) -> tuple[list[tuple[str, Decimal, str]], list[str]]:
    """Pagas extraordinarias devengadas y todavía no abonadas a la fecha de
    baja. Con 14 pagas se aplica el devengo del Convenio Metal Madrid (art.
    33): paga de julio (semestre 1/1–30/6, abono 15/7) y de diciembre
    (semestre 1/7–31/12, abono 22/12). Con otro número de pagas se supone un
    devengo anual sin abonos previos (y se avisa)."""
    if prorrateadas or numero_pagas <= 12:
        return [], []

    extras = numero_pagas - 12
    items: list[tuple[str, Decimal, str]] = []
    avisos: list[str] = []

    if extras == 2:
        anio = fecha_baja.year
        pagas = [
            ("julio", date(anio, 1, 1), date(anio, 6, 30), date(anio, 7, 15)),
            ("diciembre", date(anio, 7, 1), date(anio, 12, 31), date(anio, 12, 22)),
        ]
        for nombre, ini, fin, abono in pagas:
            if fecha_baja >= abono:
                continue  # ya abonada en su fecha
            desde = max(ini, fecha_ingreso)
            hasta = min(fin, fecha_baja)
            if desde > hasta:
                continue
            dias = (hasta - desde).days + 1
            total = (fin - ini).days + 1
            importe = _q(base_paga_mensual * Decimal(dias) / Decimal(total))
            items.append(
                (
                    f"Paga extraordinaria de {nombre} (parte devengada)",
                    importe,
                    f"{dias} de {total} días del semestre {ini:%d/%m}–{fin:%d/%m} (abono el {abono:%d/%m})",
                )
            )
    else:
        inicio = max(date(fecha_baja.year, 1, 1), fecha_ingreso)
        dias = (fecha_baja - inicio).days + 1
        dias_anio = 366 if calendar.isleap(fecha_baja.year) else 365
        importe = _q(base_paga_mensual * Decimal(extras) * Decimal(dias) / Decimal(dias_anio))
        items.append(
            (
                f"Pagas extraordinarias (parte devengada, {extras} al año)",
                importe,
                f"{dias} de {dias_anio} días del año",
            )
        )
        avisos.append(
            f"El convenio tiene {numero_pagas} pagas: se supone devengo anual de las {extras} pagas "
            "extraordinarias sin abonos previos este año. Revisa las fechas de devengo y abono de tu convenio."
        )
    return items, avisos


# ---------- cálculo completo ----------

def calcular_liquidacion(e: EntradaLiquidacion) -> ResultadoLiquidacion:
    if e.motivo not in MOTIVOS:
        raise ValueError(f"Motivo de baja no válido: {e.motivo}")
    if e.fecha_baja < e.fecha_ingreso:
        raise ValueError("La fecha de baja no puede ser anterior a la fecha de ingreso")

    c = e.convenio
    p = e.parametros
    r = ResultadoLiquidacion()
    lineas = r.lineas

    # --- bases mensuales (mes completo) ---
    dias_mes = calendar.monthrange(e.fecha_baja.year, e.fecha_baja.month)[1]
    ev_completo = EventosMes(
        periodo_anio=e.fecha_baja.year,
        periodo_mes=e.fecha_baja.month,
        dias_naturales_periodo=dias_mes,
        dias_trabajados=dias_mes,
    )
    _, mensual_total, base_paga_mensual = calcular_devengos(c, ev_completo)
    extras_anuales = max(0, c.numero_pagas - 12)
    anual_total = mensual_total * 12 + base_paga_mensual * extras_anuales
    mensual_con_prorrata = mensual_total + base_paga_mensual * extras_anuales / 12
    r.salario_diario_indemnizacion = (anual_total / Decimal(365)).quantize(Decimal("0.0001"), ROUND_HALF_UP)
    r.salario_diario_preaviso = (mensual_con_prorrata / Decimal(30)).quantize(Decimal("0.0001"), ROUND_HALF_UP)

    fin_exclusivo = e.fecha_baja + timedelta(days=1)
    r.antiguedad_texto = texto_antiguedad(e.fecha_ingreso, fin_exclusivo)

    # --- 1) salario de los días trabajados del mes de la baja ---
    if (e.fecha_ingreso.year, e.fecha_ingreso.month) == (e.fecha_baja.year, e.fecha_baja.month):
        dias_trabajados = e.fecha_baja.day - e.fecha_ingreso.day + 1
    else:
        dias_trabajados = e.fecha_baja.day
    ev_mes = EventosMes(
        periodo_anio=e.fecha_baja.year,
        periodo_mes=e.fecha_baja.month,
        dias_naturales_periodo=dias_mes,
        dias_trabajados=dias_trabajados,
    )
    lineas_salario, _, _ = calcular_devengos(c, ev_mes)
    for ls in lineas_salario:
        lineas.append(
            LineaLiquidacion(
                bloque="devengo",
                concepto=ls.concepto,
                importe=ls.importe,
                detalle=f"{dias_trabajados} de {dias_mes} días de {e.fecha_baja:%m/%Y}",
                referencia_legal=ls.referencia_legal,
                cotiza=True,
                tributa=True,
            )
        )

    # --- 2) pagas extraordinarias devengadas ---
    pagas, avisos_pagas = pagas_extra_pendientes(
        e.fecha_ingreso, e.fecha_baja, c.numero_pagas, base_paga_mensual, c.pagas_extra_prorrateadas
    )
    r.avisos.extend(avisos_pagas)
    for concepto, importe, detalle in pagas:
        lineas.append(
            LineaLiquidacion(
                bloque="devengo",
                concepto=concepto,
                importe=importe,
                detalle=detalle,
                referencia_legal="Art. 31 ET; convenio colectivo aplicable",
                cotiza=True,
                tributa=True,
            )
        )

    # --- 3) vacaciones ---
    devengadas, disfrutadas_nat, anteriores_nat, pendientes = calcular_vacaciones(
        e.fecha_ingreso,
        e.fecha_baja,
        e.vacaciones_dias_naturales,
        e.vacaciones_dias_laborables,
        e.vacaciones_disfrutadas,
        e.unidad_vacaciones,
        e.vacaciones_pendientes_anteriores,
    )
    valor_dia_vacaciones = mensual_total / Decimal(30)
    if pendientes != 0:
        importe_vac = _q(abs(pendientes) * valor_dia_vacaciones)
        detalle_vac = (
            f"{devengadas:.2f} devengados en {e.fecha_baja.year}"
            + (f" + {anteriores_nat:.2f} de años anteriores" if anteriores_nat else "")
            + f" − {disfrutadas_nat:.2f} disfrutados = {pendientes:.2f} días naturales"
            + f" × {_q(valor_dia_vacaciones):.2f} €/día"
        )
        if pendientes > 0:
            lineas.append(
                LineaLiquidacion(
                    bloque="devengo",
                    concepto=f"Vacaciones devengadas y no disfrutadas ({pendientes:.2f} días naturales)",
                    importe=importe_vac,
                    detalle=detalle_vac,
                    referencia_legal="Art. 38 ET; convenio colectivo aplicable",
                    cotiza=True,
                    tributa=True,
                )
            )
        else:
            lineas.append(
                LineaLiquidacion(
                    bloque="descuento",
                    concepto=f"Vacaciones disfrutadas en exceso ({abs(pendientes):.2f} días naturales)",
                    importe=importe_vac,
                    detalle=detalle_vac,
                    referencia_legal="Art. 38 ET (compensación de lo ya disfrutado)",
                )
            )
            r.avisos.append(
                "Se han disfrutado más vacaciones de las devengadas: el exceso se descuenta de la liquidación. "
                "Comprueba que el convenio o el contrato permiten ese descuento."
            )

    # --- 4) preaviso ---
    omitidos = max(0, e.dias_preaviso_exigidos - e.dias_preaviso_trabajados)
    if omitidos:
        importe_preaviso = _q(Decimal(omitidos) * r.salario_diario_preaviso)
        detalle_preaviso = (
            f"{omitidos} días omitidos ({e.dias_preaviso_exigidos} exigidos − {e.dias_preaviso_trabajados} cumplidos)"
            f" × {_q(r.salario_diario_preaviso):.2f} €/día (con prorrata de pagas extra)"
        )
        if e.motivo == "dimision":
            lineas.append(
                LineaLiquidacion(
                    bloque="descuento",
                    concepto=f"Descuento por preaviso incumplido ({omitidos} días)",
                    importe=importe_preaviso,
                    detalle=detalle_preaviso,
                    referencia_legal="Art. 49.1.d ET y convenio colectivo (descuento del salario de los días de preaviso omitidos)",
                )
            )
        elif e.motivo in ("despido_objetivo", "fin_contrato_temporal"):
            lineas.append(
                LineaLiquidacion(
                    bloque="devengo",
                    concepto=f"Compensación por preaviso no concedido ({omitidos} días)",
                    importe=importe_preaviso,
                    detalle=detalle_preaviso,
                    referencia_legal=(
                        "Art. 53.1.c ET (despido objetivo)"
                        if e.motivo == "despido_objetivo"
                        else "Art. 49.1.c ET (fin de contrato temporal de más de un año)"
                    ),
                    cotiza=True,
                    tributa=True,
                )
            )
            r.avisos.append(
                "La compensación por preaviso no concedido cotiza a la Seguridad Social (criterio de la TGSS, "
                "boletín RED 08/2026) y tributa por IRPF: no es indemnización exenta."
            )
        else:
            r.avisos.append("El motivo de baja elegido no genera obligación de preaviso: los días indicados se ignoran.")

    # --- 5) indemnización ---
    tipo_contrato = (c.tipo_contrato or "").lower()
    indemnizacion = None
    if e.motivo == "fin_contrato_temporal" and tipo_contrato in ("indefinido", "formacion", "practicas"):
        r.avisos.append(
            "El contrato registrado es "
            + ("indefinido: el fin de un contrato temporal no aplica." if tipo_contrato == "indefinido"
               else "formativo: no genera la indemnización de 12 días por año.")
        )
    else:
        indemnizacion = calcular_indemnizacion(
            e.motivo, e.fecha_ingreso, e.fecha_baja, r.salario_diario_indemnizacion
        )
    if indemnizacion is not None:
        r.indemnizacion_legal = indemnizacion.importe
        exenta = min(indemnizacion.importe, LIMITE_EXENCION_IRPF_INDEMNIZACION)
        exceso = indemnizacion.importe - exenta
        r.indemnizacion_exenta = exenta
        lineas.append(
            LineaLiquidacion(
                bloque="indemnizacion",
                concepto=f"Indemnización por {MOTIVOS[e.motivo].split(' (')[0].lower()}",
                importe=exenta,
                detalle=f"{indemnizacion.detalle} × {_q(r.salario_diario_indemnizacion):.2f} €/día "
                f"(antigüedad {r.antiguedad_texto})",
                referencia_legal=indemnizacion.referencia_legal
                + "; exenta de IRPF (art. 7.e LIRPF) y de cotización (art. 147.2.c LGSS)",
            )
        )
        if exceso > 0:
            lineas.append(
                LineaLiquidacion(
                    bloque="indemnizacion",
                    concepto="Exceso de la indemnización sobre el límite exento de 180.000 €",
                    importe=exceso,
                    referencia_legal="Art. 7.e LIRPF",
                    tributa=True,
                )
            )
    if e.motivo == "despido_improcedente":
        r.avisos.append(
            "Indemnización calculada con la ley vigente (33 días por año, máx. 24 mensualidades). La reforma del "
            "despido improcedente está en negociación en 2026 y todavía no ha sido aprobada: si cambia, hay que revisarla."
        )
    if e.indemnizacion_pactada > 0:
        lineas.append(
            LineaLiquidacion(
                bloque="indemnizacion",
                concepto="Indemnización pactada (mutuo acuerdo o exceso sobre la legal)",
                importe=_q(e.indemnizacion_pactada),
                detalle="Se trata como sujeta a cotización e IRPF salvo que se acredite que está exenta.",
                referencia_legal="Art. 7.e LIRPF y art. 147.2 LGSS: solo está exenta la indemnización legalmente obligatoria",
                cotiza=True,
                tributa=True,
            )
        )

    # --- 6) otras cantidades y descuentos libres ---
    if e.otras_cantidades > 0:
        lineas.append(
            LineaLiquidacion(
                bloque="devengo",
                concepto="Otras cantidades pendientes de abonar",
                importe=_q(e.otras_cantidades),
                detalle="Horas extra, pluses, promedio de conceptos variables de vacaciones, etc.",
                referencia_legal="Art. 26 ET",
                cotiza=True,
                tributa=True,
            )
        )
    if e.descuentos > 0:
        lineas.append(
            LineaLiquidacion(
                bloque="descuento",
                concepto="Descuentos pendientes (anticipos, préstamos, material...)",
                importe=_q(e.descuentos),
                referencia_legal="Art. 29.1 ET (anticipos); resto según pacto",
            )
        )

    # --- 7) bases, cotización e IRPF ---
    r.base_cotizacion = sum((l.importe for l in lineas if l.cotiza), Decimal("0"))
    r.base_irpf = sum((l.importe for l in lineas if l.tributa), Decimal("0"))

    pct_trabajador = (
        p.tipo_cc_trabajador_pct + p.tipo_desempleo_trabajador_pct + p.tipo_fp_trabajador_pct + p.tipo_mei_trabajador_pct
    )
    pct_empresa = (
        p.tipo_cc_empresa_pct
        + p.tipo_desempleo_empresa_pct
        + p.tipo_fp_empresa_pct
        + p.tipo_fogasa_empresa_pct
        + p.tipo_mei_empresa_pct
        + c.tipo_at_ep_pct
    )
    # Solo se aplica el tope máximo: la base mínima del grupo es para un mes
    # completo y no tiene sentido en una liquidación de pocos días.
    base_ss = min(r.base_cotizacion, p.tope_max_mensual) if p.tope_max_mensual else r.base_cotizacion
    r.cotizacion_trabajador = _q(base_ss * pct_trabajador / Decimal(100))
    r.cuota_empresa_ss = _q(base_ss * pct_empresa / Decimal(100))
    if r.base_cotizacion > base_ss:
        r.avisos.append("La base de cotización supera el tope máximo mensual: solo se cotiza hasta el tope.")

    # Tipo de retención de una nómina ordinaria de este trabajador.
    base_regular = min(mensual_total, p.tope_max_mensual) if p.tope_max_mensual else mensual_total
    cuota_ss_regular = _q(base_regular * pct_trabajador / Decimal(100))
    lineas_irpf, _ = calcular_irpf(
        mensual_total,
        cuota_ss_regular,
        c.numero_pagas,
        e.hijos_menores_25,
        e.grado_discapacidad,
        e.tramos_irpf,
        e.edad,
    )
    r.tipo_irpf_pct = lineas_irpf[0].tipo_pct if lineas_irpf and lineas_irpf[0].tipo_pct is not None else Decimal("0")
    r.retencion_irpf = _q(r.base_irpf * r.tipo_irpf_pct / Decimal(100))
    if not e.tramos_irpf:
        r.avisos.append("No hay tabla de IRPF cargada para este año: no se ha calculado la retención.")

    lineas.append(
        LineaLiquidacion(
            bloque="deduccion",
            concepto="Cotización a la Seguridad Social (trabajador)",
            importe=r.cotizacion_trabajador,
            detalle=f"{_q(pct_trabajador):.2f}% sobre {_q(base_ss):.2f} €",
            referencia_legal="Art. 144 y ss. LGSS",
        )
    )
    lineas.append(
        LineaLiquidacion(
            bloque="deduccion",
            concepto=f"Retención de IRPF ({r.tipo_irpf_pct:.2f}%)",
            importe=r.retencion_irpf,
            detalle=f"{r.tipo_irpf_pct:.2f}% sobre {_q(r.base_irpf):.2f} € sujetos a IRPF (la indemnización exenta no entra)",
            referencia_legal="Arts. 80-87 Reglamento IRPF",
        )
    )

    # --- 8) totales ---
    r.total_ingresos = _q(sum((l.importe for l in lineas if l.bloque in ("devengo", "indemnizacion")), Decimal("0")))
    r.total_descuentos = _q(sum((l.importe for l in lineas if l.bloque == "descuento"), Decimal("0")))
    r.total_deducciones = _q(r.cotizacion_trabajador + r.retencion_irpf + r.total_descuentos)
    r.liquido_a_percibir = _q(r.total_ingresos - r.total_deducciones)
    r.coste_empresa_total = _q(r.total_ingresos - r.total_descuentos + r.cuota_empresa_ss)

    # --- avisos generales ---
    if "EJEMPLO" in (c.nombre_convenio or "").upper():
        r.avisos.append(
            "El convenio de este contrato es de EJEMPLO: las vacaciones y el preaviso usan valores genéricos. "
            "Sustitúyelos por los de tu convenio real."
        )
    r.avisos.append(
        "Las vacaciones se pagan con el salario de convenio, antigüedad y mejoras fijas; si el convenio exige añadir "
        "el promedio de conceptos variables de los últimos 3 meses (como el art. 35 del Convenio Metal), no se "
        "calcula aquí: añádelo en «Otras cantidades»."
    )
    if pendientes > 0:
        r.avisos.append(
            "Los días de vacaciones no disfrutados mantienen al trabajador de alta en la Seguridad Social: "
            "la fecha de baja en el sistema RED se retrasa esos días."
        )
    r.avisos.append("Cálculo orientativo: confírmalo con tu asesoría laboral antes de firmar el finiquito.")
    return r
