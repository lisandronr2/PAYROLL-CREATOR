"""
Motor de cálculo de nómina española (MVP).

IMPORTANTE — alcance y simplificaciones (ver docs/LEGAL_DISCLAIMER.md):
Este motor reproduce la ESTRUCTURA legal del cálculo (devengos, cotización con
topes por grupo, IRPF por el procedimiento general simplificado, IT, horas
extra, prorrata de pagas extra) pero varias reglas se han simplificado para
un primer MVP y DEBEN ser revisadas por una asesoría antes de un uso en
producción real:
  - Horas extra: se cotizan con los mismos tipos generales (en la práctica
    tienen una cotización adicional específica distinta a la general).
  - IT: se muestra el importe total teórico (60%/75% de la base reguladora
    diaria) sin gestionar el circuito de pago delegado/reembolso INSS-mutua.
  - IRPF: se usa el procedimiento general simplificado (tabla de tramos +
    reducción fija por hijos/discapacidad), no el cálculo íntegro del
    Reglamento IRPF (arts. 80-88) con todas las circunstancias personales.
  - Embargos: se aplica el límite de inembargabilidad del SMI de forma
    simplificada, no la escala completa del art. 607 LEC.

Cada línea de resultado (`LineaCalculo`) incluye su referencia legal para
que el futuro "modo auditor" pueda explicarla.
"""
from decimal import Decimal, ROUND_HALF_UP

from app.engine.tipos import (
    DatosConvenioContrato,
    EventosMes,
    LineaCalculo,
    ParametrosCotizacion,
    ResultadoNomina,
)

TWO = Decimal("0.01")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(TWO, rounding=ROUND_HALF_UP)


def _dias_trabajados_normales(eventos: EventosMes) -> int:
    if eventos.dias_trabajados is not None:
        return eventos.dias_trabajados
    return max(0, eventos.dias_naturales_periodo - eventos.dias_it)


def _precio_unitario(importe: Decimal, cantidad: Decimal) -> Decimal | None:
    if not cantidad:
        return None
    return (importe / cantidad).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calcular_devengos(
    convenio: DatosConvenioContrato, eventos: EventosMes
) -> tuple[list[LineaCalculo], Decimal]:
    """Devuelve las líneas de devengo y la suma base (sin horas extra/IT) prorateada por jornada y días."""
    lineas: list[LineaCalculo] = []
    pct_jornada = convenio.jornada_porcentaje / Decimal(100)

    salario_mensual_base = convenio.salario_pactado_mensual or convenio.salario_convenio_mensual
    salario_base = salario_mensual_base * pct_jornada
    complemento_antiguedad = (
        convenio.valor_quinquenio_o_trienio * convenio.numero_quinquenios_o_trienios * pct_jornada
    )
    plus_convenio = convenio.plus_convenio_mensual * pct_jornada
    complemento_mensual = convenio.complemento_mensual * pct_jornada

    dias_trabajados = _dias_trabajados_normales(eventos)
    cantidad_dias = Decimal(dias_trabajados)
    factor_dias = (
        cantidad_dias / Decimal(eventos.dias_naturales_periodo)
        if eventos.dias_naturales_periodo
        else Decimal(1)
    )

    salario_base_prorateado = _q(salario_base * factor_dias)
    antiguedad_prorateada = _q(complemento_antiguedad * factor_dias)
    plus_convenio_prorateado = _q(plus_convenio * factor_dias)
    complemento_mensual_prorateado = _q(complemento_mensual * factor_dias)

    lineas.append(
        LineaCalculo(
            bloque="devengo",
            concepto="Salario base convenio",
            cantidad=cantidad_dias,
            base=_precio_unitario(salario_base_prorateado, cantidad_dias),
            tipo_pct=None,
            importe=salario_base_prorateado,
            referencia_legal=f"Tabla salarial {convenio.nombre_convenio}, jornada {convenio.jornada_porcentaje}%",
        )
    )
    if antiguedad_prorateada:
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto="Complemento de antigüedad (trienio/quinquenio)",
                cantidad=cantidad_dias,
                base=_precio_unitario(antiguedad_prorateada, cantidad_dias),
                importe=antiguedad_prorateada,
                referencia_legal="Art. 25 Estatuto de los Trabajadores; convenio colectivo aplicable",
            )
        )
    if plus_convenio_prorateado:
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto="Plus convenio",
                cantidad=cantidad_dias,
                base=_precio_unitario(plus_convenio_prorateado, cantidad_dias),
                importe=plus_convenio_prorateado,
                referencia_legal=f"Tabla salarial {convenio.nombre_convenio}",
            )
        )
    if complemento_mensual_prorateado:
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto="Mejora voluntaria",
                cantidad=cantidad_dias,
                base=_precio_unitario(complemento_mensual_prorateado, cantidad_dias),
                importe=complemento_mensual_prorateado,
                referencia_legal="Art. 27 Estatuto de los Trabajadores (mejora voluntaria pactada, sujeta a cotización e IRPF)",
            )
        )

    suma_base = (
        salario_base_prorateado
        + antiguedad_prorateada
        + plus_convenio_prorateado
        + complemento_mensual_prorateado
    )
    # Base para la prorrata de pagas extraordinarias: solo los conceptos de
    # convenio (salario, antigüedad, plus convenio). La mejora voluntaria
    # queda fuera salvo que el contrato/convenio diga expresamente lo
    # contrario, igual que en un recibo de nómina real.
    base_pagas_extra = salario_base_prorateado + antiguedad_prorateada + plus_convenio_prorateado
    return lineas, suma_base, base_pagas_extra


def calcular_horas_extra_y_nocturnidad(
    convenio: DatosConvenioContrato,
    eventos: EventosMes,
    parametros: ParametrosCotizacion,
) -> tuple[list[LineaCalculo], Decimal]:
    lineas: list[LineaCalculo] = []
    total = Decimal("0")

    base_hora = convenio.base_calculo_complementos_mensual or convenio.salario_convenio_mensual
    precio_hora_ordinaria = Decimal("0")
    if convenio.jornada_anual_horas:
        precio_hora_ordinaria = _q((base_hora * 12) / convenio.jornada_anual_horas)

    if eventos.horas_extra and precio_hora_ordinaria:
        recargo = Decimal(1) + parametros.recargo_hora_extra_pct / Decimal(100)
        importe = _q(eventos.horas_extra * precio_hora_ordinaria * recargo)
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"Horas extraordinarias ({eventos.horas_extra}h)",
                cantidad=eventos.horas_extra,
                base=precio_hora_ordinaria,
                tipo_pct=parametros.recargo_hora_extra_pct,
                importe=importe,
                referencia_legal="Art. 35 Estatuto de los Trabajadores (recargo mínimo 75% h. ordinaria, o el pactado en convenio)",
            )
        )

    if eventos.horas_extra_nocturnas and precio_hora_ordinaria:
        recargo = Decimal(1) + (
            parametros.recargo_hora_extra_pct + parametros.plus_nocturnidad_pct
        ) / Decimal(100)
        importe = _q(eventos.horas_extra_nocturnas * precio_hora_ordinaria * recargo)
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"Horas extraordinarias nocturnas ({eventos.horas_extra_nocturnas}h)",
                cantidad=eventos.horas_extra_nocturnas,
                base=precio_hora_ordinaria,
                importe=importe,
                referencia_legal="Art. 35 y 36 Estatuto de los Trabajadores",
            )
        )

    if eventos.horas_nocturnas_ordinarias and precio_hora_ordinaria:
        importe = _q(
            eventos.horas_nocturnas_ordinarias
            * precio_hora_ordinaria
            * (parametros.plus_nocturnidad_pct / Decimal(100))
        )
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"Plus de nocturnidad ({eventos.horas_nocturnas_ordinarias}h)",
                cantidad=eventos.horas_nocturnas_ordinarias,
                base=precio_hora_ordinaria,
                tipo_pct=parametros.plus_nocturnidad_pct,
                importe=importe,
                referencia_legal="Art. 36 Estatuto de los Trabajadores",
            )
        )

    if eventos.dias_festivos_trabajados:
        salario_dia = _q((base_hora * 12) / Decimal(365))
        recargo = Decimal(1) + parametros.recargo_hora_extra_pct / Decimal(100)
        importe = _q(Decimal(eventos.dias_festivos_trabajados) * salario_dia * recargo)
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"Festivos trabajados ({eventos.dias_festivos_trabajados} días)",
                cantidad=Decimal(eventos.dias_festivos_trabajados),
                base=salario_dia,
                tipo_pct=parametros.recargo_hora_extra_pct,
                importe=importe,
                referencia_legal="Convenio colectivo aplicable (descanso semanal/festivos, art. 37 ET)",
            )
        )

    return lineas, total


def calcular_it(
    convenio: DatosConvenioContrato, eventos: EventosMes, suma_devengos_base: Decimal
) -> tuple[list[LineaCalculo], Decimal]:
    """Prestación por Incapacidad Temporal (contingencia común, simplificado)."""
    if not eventos.dias_it:
        return [], Decimal("0")

    base_reguladora_diaria = _q(suma_devengos_base / Decimal(30)) if suma_devengos_base else Decimal("0")
    dias_sin_prestacion = min(eventos.dias_it, 3)
    dias_60pct = max(0, min(eventos.dias_it, 20) - 3)
    dias_75pct = max(0, eventos.dias_it - 20)

    lineas = []
    total = Decimal("0")

    if dias_sin_prestacion:
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"IT días 1-3 sin prestación ({dias_sin_prestacion} días, salvo mejora de convenio)",
                importe=Decimal("0.00"),
                referencia_legal="Art. 173 LGSS; ver mejora voluntaria en convenio aplicable",
                cotiza=False,
            )
        )
    if dias_60pct:
        importe = _q(base_reguladora_diaria * Decimal("0.60") * dias_60pct)
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"IT días 4-20 al 60% base reguladora ({dias_60pct} días)",
                base=base_reguladora_diaria,
                tipo_pct=Decimal("60"),
                importe=importe,
                referencia_legal="Art. 173 LGSS",
                cotiza=False,
            )
        )
    if dias_75pct:
        importe = _q(base_reguladora_diaria * Decimal("0.75") * dias_75pct)
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"IT desde día 21 al 75% base reguladora ({dias_75pct} días)",
                base=base_reguladora_diaria,
                tipo_pct=Decimal("75"),
                importe=importe,
                referencia_legal="Art. 173 LGSS",
                cotiza=False,
            )
        )
    return lineas, total


def calcular_prorrata_pagas_extra(
    convenio: DatosConvenioContrato, suma_devengos_base: Decimal
) -> tuple[LineaCalculo | None, Decimal, Decimal]:
    """
    Devuelve (línea si se paga, importe que se abona en la nómina, importe que
    computa a efectos de cotización aunque no se abone ahora).
    Art. 109 LGSS: las pagas extraordinarias siempre se prorratean en la base
    de cotización mensual, se paguen o no prorrateadas en nómina.
    """
    if convenio.numero_pagas <= 12:
        return None, Decimal("0"), Decimal("0")

    pagas_extra_anuales = convenio.numero_pagas - 12
    importe_prorrata = _q(suma_devengos_base * pagas_extra_anuales / Decimal(12))

    if convenio.pagas_extra_prorrateadas:
        linea = LineaCalculo(
            bloque="devengo",
            concepto="Prorrata de pagas extraordinarias",
            cantidad=Decimal("1"),
            base=importe_prorrata,
            importe=importe_prorrata,
            referencia_legal="Art. 31 Estatuto de los Trabajadores (prorrateo pactado)",
        )
        return linea, importe_prorrata, importe_prorrata

    # No prorrateada: no se paga en la nómina mensual, pero cotiza igualmente.
    return None, Decimal("0"), importe_prorrata


def calcular_dietas(
    convenio: DatosConvenioContrato, eventos: EventosMes
) -> tuple[list[LineaCalculo], Decimal]:
    """
    Dietas de manutención/desplazamiento según el convenio del contrato.
    Son una compensación de gastos, no salario: quedan fuera de la base de
    cotización y de la base de IRPF hasta los límites reglamentarios (art. 9
    Reglamento IRPF, RD 439/2007; Orden de cotización a la SS). Este MVP las
    trata como exentas en su totalidad — comprueba que el importe total no
    supere esos límites antes de usarlo en una nómina real.
    """
    lineas: list[LineaCalculo] = []
    total = Decimal("0")

    if eventos.numero_medias_dietas and convenio.media_dieta:
        importe = _q(convenio.media_dieta * eventos.numero_medias_dietas)
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=f"Media dieta ({eventos.numero_medias_dietas} días) — {convenio.nombre_convenio}",
                cantidad=Decimal(eventos.numero_medias_dietas),
                base=convenio.media_dieta,
                importe=importe,
                referencia_legal="Convenio colectivo aplicable; exenta hasta límites del art. 9 Reglamento IRPF",
                cotiza=False,
            )
        )

    if eventos.numero_dietas_completas_cortas and convenio.dieta_completa_corta:
        importe = _q(convenio.dieta_completa_corta * eventos.numero_dietas_completas_cortas)
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=(
                    f"Dieta completa, viaje < 7 días ({eventos.numero_dietas_completas_cortas} días) "
                    f"— {convenio.nombre_convenio}"
                ),
                cantidad=Decimal(eventos.numero_dietas_completas_cortas),
                base=convenio.dieta_completa_corta,
                importe=importe,
                referencia_legal="Convenio colectivo aplicable; exenta hasta límites del art. 9 Reglamento IRPF",
                cotiza=False,
            )
        )

    if eventos.numero_dietas_completas_largas and convenio.dieta_completa_larga:
        importe = _q(convenio.dieta_completa_larga * eventos.numero_dietas_completas_largas)
        total += importe
        lineas.append(
            LineaCalculo(
                bloque="devengo",
                concepto=(
                    f"Dieta completa, viaje ≥ 7 días ({eventos.numero_dietas_completas_largas} días) "
                    f"— {convenio.nombre_convenio}"
                ),
                cantidad=Decimal(eventos.numero_dietas_completas_largas),
                base=convenio.dieta_completa_larga,
                importe=importe,
                referencia_legal="Convenio colectivo aplicable; exenta hasta límites del art. 9 Reglamento IRPF",
                cotiza=False,
            )
        )

    return lineas, total


def calcular_cotizacion(
    parametros: ParametrosCotizacion, base_bruta_cotizable: Decimal, tipo_at_ep_pct: Decimal = Decimal("0")
) -> tuple[list[LineaCalculo], Decimal, Decimal, Decimal]:
    """Aplica topes de grupo y calcula cuotas trabajador/empresa.

    Devuelve (líneas, base_ajustada, cuota_trabajador_total, cuota_empresa_total).
    """
    base_ajustada = base_bruta_cotizable
    if parametros.tope_max_mensual and base_ajustada > parametros.tope_max_mensual:
        base_ajustada = parametros.tope_max_mensual
    if parametros.tope_min_grupo_mensual and base_ajustada < parametros.tope_min_grupo_mensual:
        base_ajustada = parametros.tope_min_grupo_mensual
    base_ajustada = _q(base_ajustada)

    lineas: list[LineaCalculo] = []

    conceptos_trabajador = [
        ("Contingencias comunes (trabajador)", parametros.tipo_cc_trabajador_pct, "Art. 144 LGSS; Orden anual de cotización"),
        ("Desempleo (trabajador)", parametros.tipo_desempleo_trabajador_pct, "Art. 227 y ss. LGSS"),
        ("Formación profesional (trabajador)", parametros.tipo_fp_trabajador_pct, "Orden anual de cotización"),
        ("MEI - Mecanismo de Equidad Intergeneracional (trabajador)", parametros.tipo_mei_trabajador_pct, "DA 21ª LGSS (Ley 21/2021)"),
    ]
    conceptos_empresa = [
        ("Contingencias comunes (empresa)", parametros.tipo_cc_empresa_pct, "Art. 144 LGSS; Orden anual de cotización"),
        ("Desempleo (empresa)", parametros.tipo_desempleo_empresa_pct, "Art. 227 y ss. LGSS"),
        ("Formación profesional (empresa)", parametros.tipo_fp_empresa_pct, "Orden anual de cotización"),
        ("FOGASA (empresa)", parametros.tipo_fogasa_empresa_pct, "Art. 33 Estatuto de los Trabajadores"),
        ("MEI - Mecanismo de Equidad Intergeneracional (empresa)", parametros.tipo_mei_empresa_pct, "DA 21ª LGSS (Ley 21/2021)"),
        (
            "Contingencias profesionales - AT y EP (empresa)",
            tipo_at_ep_pct,
            "DA 61ª LGSS; tarifa de primas (RD-ley 16/2025) según CNAE/epígrafe de la empresa — verificar el tipo aplicable",
        ),
    ]

    cuota_trabajador_total = Decimal("0")
    for concepto, pct, ref in conceptos_trabajador:
        importe = _q(base_ajustada * pct / Decimal(100))
        cuota_trabajador_total += importe
        lineas.append(
            LineaCalculo(
                bloque="cotizacion_trabajador",
                concepto=concepto,
                base=base_ajustada,
                tipo_pct=pct,
                importe=importe,
                referencia_legal=ref,
            )
        )

    cuota_empresa_total = Decimal("0")
    for concepto, pct, ref in conceptos_empresa:
        importe = _q(base_ajustada * pct / Decimal(100))
        cuota_empresa_total += importe
        lineas.append(
            LineaCalculo(
                bloque="cotizacion_empresa",
                concepto=concepto,
                base=base_ajustada,
                tipo_pct=pct,
                importe=importe,
                referencia_legal=ref,
            )
        )

    return lineas, base_ajustada, cuota_trabajador_total, cuota_empresa_total


def calcular_irpf(
    base_mensual_irpf: Decimal,
    numero_pagas: int,
    hijos_menores_25: int,
    grado_discapacidad: int,
    tramos: list[tuple[Decimal, Decimal | None, Decimal]],
) -> tuple[list[LineaCalculo], Decimal]:
    """
    Procedimiento general simplificado (art. 82-87 Reglamento IRPF):
    1) Se estima la base anual a partir de la mensual.
    2) Se reduce por mínimo familiar simplificado (hijos/discapacidad).
    3) Se calcula la cuota íntegra aplicando la tarifa por tramos.
    4) El tipo de retención = cuota íntegra / base anual, aplicado a la base mensual.
    `tramos`: lista de (base_desde_anual, base_hasta_anual|None, tipo_pct) ordenada ascendente.
    """
    if base_mensual_irpf <= 0 or not tramos:
        return [], Decimal("0")

    base_anual_estimada = base_mensual_irpf * numero_pagas

    reduccion_hijos = Decimal(hijos_menores_25) * Decimal("2400")  # simplificado, orientativo
    reduccion_discapacidad = Decimal("3000") if grado_discapacidad >= 33 else Decimal("0")
    base_anual_ajustada = max(Decimal("0"), base_anual_estimada - reduccion_hijos - reduccion_discapacidad)

    cuota_integra = Decimal("0")
    for desde, hasta, tipo_pct in tramos:
        techo_tramo = hasta if hasta is not None else base_anual_ajustada
        if base_anual_ajustada <= desde:
            break
        base_en_tramo = min(base_anual_ajustada, techo_tramo) - desde
        if base_en_tramo > 0:
            cuota_integra += base_en_tramo * tipo_pct / Decimal(100)

    tipo_medio = (cuota_integra / base_anual_estimada) if base_anual_estimada > 0 else Decimal("0")
    tipo_medio = tipo_medio.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    retencion_mensual = _q(base_mensual_irpf * tipo_medio)

    linea = LineaCalculo(
        bloque="deduccion",
        concepto="Retención IRPF",
        base=base_mensual_irpf,
        tipo_pct=(tipo_medio * 100).quantize(Decimal("0.01")),
        importe=retencion_mensual,
        referencia_legal="Arts. 80-87 Reglamento IRPF (RD 439/2007); procedimiento general simplificado",
    )
    return [linea], retencion_mensual


def calcular_deducciones_varias(
    eventos: EventosMes, liquido_previo: Decimal, smi_mensual: Decimal
) -> tuple[list[LineaCalculo], Decimal]:
    lineas: list[LineaCalculo] = []
    total = Decimal("0")

    if eventos.anticipos:
        lineas.append(
            LineaCalculo(
                bloque="deduccion",
                concepto="Anticipo a cuenta",
                importe=_q(eventos.anticipos),
                referencia_legal="Art. 29.1 Estatuto de los Trabajadores",
            )
        )
        total += _q(eventos.anticipos)

    if eventos.embargo_mensual:
        # Simplificación del límite de inembargabilidad: solo se embarga el
        # exceso sobre el SMI mensual (la escala real es progresiva, art. 607 LEC).
        margen_embargable = max(Decimal("0"), liquido_previo - total - smi_mensual)
        importe_embargo = min(eventos.embargo_mensual, margen_embargable)
        if importe_embargo:
            lineas.append(
                LineaCalculo(
                    bloque="deduccion",
                    concepto="Embargo judicial/administrativo",
                    importe=_q(importe_embargo),
                    referencia_legal="Art. 607 Ley de Enjuiciamiento Civil (límite de inembargabilidad del SMI, simplificado)",
                )
            )
            total += _q(importe_embargo)

    return lineas, total


def calcular_nomina(
    convenio: DatosConvenioContrato,
    eventos: EventosMes,
    parametros: ParametrosCotizacion,
    tramos_irpf: list[tuple[Decimal, Decimal | None, Decimal]],
    hijos_menores_25: int = 0,
    grado_discapacidad: int = 0,
) -> ResultadoNomina:
    resultado = ResultadoNomina()

    lineas_devengo_base, suma_devengos_base, base_pagas_extra = calcular_devengos(convenio, eventos)
    lineas_horas, importe_horas = calcular_horas_extra_y_nocturnidad(convenio, eventos, parametros)
    lineas_it, importe_it = calcular_it(convenio, eventos, suma_devengos_base)
    linea_prorrata, importe_prorrata_pagado, importe_prorrata_cotizable = calcular_prorrata_pagas_extra(
        convenio, base_pagas_extra
    )
    lineas_dietas, importe_dietas = calcular_dietas(convenio, eventos)

    resultado.lineas.extend(lineas_devengo_base)
    resultado.lineas.extend(lineas_horas)
    resultado.lineas.extend(lineas_it)
    if linea_prorrata:
        resultado.lineas.append(linea_prorrata)
    resultado.lineas.extend(lineas_dietas)
    resultado.total_dietas_exentas = _q(importe_dietas)

    total_devengado = (
        suma_devengos_base + importe_horas + importe_it + importe_prorrata_pagado + importe_dietas
    )
    resultado.total_devengado = _q(total_devengado)

    base_cotizable = suma_devengos_base + importe_horas + importe_prorrata_cotizable
    lineas_cotizacion, base_ajustada, cuota_trabajador, cuota_empresa = calcular_cotizacion(
        parametros, base_cotizable, convenio.tipo_at_ep_pct
    )
    resultado.lineas.extend(lineas_cotizacion)
    resultado.base_cotizacion_comun = base_ajustada

    # Las dietas no forman parte de la base de IRPF (compensan gastos, no son
    # retribución) — se descuentan del devengado antes de calcular la retención.
    base_irpf = max(Decimal("0"), resultado.total_devengado - importe_dietas - cuota_trabajador)
    resultado.base_sujeta_irpf = _q(base_irpf)
    lineas_irpf, importe_irpf = calcular_irpf(
        base_irpf, convenio.numero_pagas, hijos_menores_25, grado_discapacidad, tramos_irpf
    )
    resultado.lineas.extend(lineas_irpf)

    lineas_ss_deduccion = [
        LineaCalculo(
            bloque="deduccion",
            concepto="Cotizaciones Seguridad Social (trabajador)",
            importe=cuota_trabajador,
            referencia_legal="Art. 144 y ss. LGSS",
        )
    ]
    resultado.lineas.extend(lineas_ss_deduccion)

    liquido_previo = resultado.total_devengado - cuota_trabajador - importe_irpf
    lineas_varias, importe_varias = calcular_deducciones_varias(
        eventos, liquido_previo, parametros.smi_mensual
    )
    resultado.lineas.extend(lineas_varias)

    resultado.total_deducciones = _q(cuota_trabajador + importe_irpf + importe_varias)
    resultado.liquido_a_percibir = _q(resultado.total_devengado - resultado.total_deducciones)
    resultado.coste_empresa_total = _q(resultado.total_devengado + cuota_empresa)

    return resultado
