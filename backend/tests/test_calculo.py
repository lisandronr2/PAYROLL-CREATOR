from decimal import Decimal

from app.engine.calculo import calcular_nomina
from app.engine.tipos import DatosConvenioContrato, EventosMes, ParametrosCotizacion

# Tramos IRPF 2026 orientativos (mismos que app/seed/parametros_legales.py)
TRAMOS_IRPF_2026 = [
    (Decimal("0"), Decimal("12450"), Decimal("19")),
    (Decimal("12450"), Decimal("20200"), Decimal("24")),
    (Decimal("20200"), Decimal("35200"), Decimal("30")),
    (Decimal("35200"), Decimal("60000"), Decimal("37")),
    (Decimal("60000"), Decimal("300000"), Decimal("45")),
    (Decimal("300000"), None, Decimal("47")),
]


def parametros_2026(grupo=5):
    topes_min_por_grupo = {
        1: Decimal("1929.00"), 2: Decimal("1929.00"), 3: Decimal("1679.40"),
        4: Decimal("1466.40"), 5: Decimal("1466.40"), 6: Decimal("1466.40"),
        7: Decimal("1466.40"),
    }
    return ParametrosCotizacion(
        tipo_cc_empresa_pct=Decimal("23.60"),
        tipo_cc_trabajador_pct=Decimal("4.70"),
        tipo_desempleo_empresa_pct=Decimal("5.50"),
        tipo_desempleo_trabajador_pct=Decimal("1.55"),
        tipo_fp_empresa_pct=Decimal("0.60"),
        tipo_fp_trabajador_pct=Decimal("0.10"),
        tipo_fogasa_empresa_pct=Decimal("0.20"),
        tipo_mei_empresa_pct=Decimal("0.75"),
        tipo_mei_trabajador_pct=Decimal("0.15"),
        tope_min_grupo_mensual=topes_min_por_grupo[grupo],
        tope_max_mensual=Decimal("4909.50"),
        smi_mensual=Decimal("1184.00"),
        recargo_hora_extra_pct=Decimal("75"),
        recargo_hora_extra_nocturna_pct=Decimal("100"),
        plus_nocturnidad_pct=Decimal("25"),
    )


def convenio_metal_grupo5(**overrides):
    base = dict(
        nombre_convenio="Metal Madrid 2026",
        numero_pagas=14,
        jornada_anual_horas=Decimal("1750"),
        salario_convenio_mensual=Decimal("1590.26"),
        base_calculo_complementos_mensual=Decimal("1590.26"),
        valor_quinquenio_o_trienio=Decimal("26.46"),
        plus_convenio_mensual=Decimal("0"),
        jornada_porcentaje=Decimal("100"),
        tipo_contrato="indefinido",
        pagas_extra_prorrateadas=False,
        numero_quinquenios_o_trienios=0,
        grupo_cotizacion=5,
        salario_pactado_mensual=None,
        media_dieta=Decimal("12.14"),
        dieta_completa_corta=Decimal("59.17"),
        dieta_completa_larga=Decimal("47.36"),
        tipo_at_ep_pct=Decimal("2.00"),
    )
    base.update(overrides)
    return DatosConvenioContrato(**base)


def test_at_ep_cotiza_100_por_ciento_a_cargo_de_la_empresa():
    convenio = convenio_metal_grupo5(tipo_at_ep_pct=Decimal("2.00"))
    eventos = EventosMes(periodo_anio=2026, periodo_mes=6, dias_naturales_periodo=30)
    resultado = calcular_nomina(convenio, eventos, parametros_2026(), TRAMOS_IRPF_2026)

    linea_at_ep = next(l for l in resultado.lineas if "AT y EP" in l.concepto)
    assert linea_at_ep.bloque == "cotizacion_empresa"
    assert linea_at_ep.tipo_pct == Decimal("2.00")
    assert linea_at_ep.importe == (resultado.base_cotizacion_comun * Decimal("2.00") / 100).quantize(Decimal("0.01"))
    # No debe existir una línea equivalente a cargo del trabajador
    assert not any("AT y EP" in l.concepto for l in resultado.lineas if l.bloque == "cotizacion_trabajador")


def test_mes_completo_sin_incidencias():
    convenio = convenio_metal_grupo5()
    eventos = EventosMes(periodo_anio=2026, periodo_mes=6, dias_naturales_periodo=30)
    resultado = calcular_nomina(convenio, eventos, parametros_2026(), TRAMOS_IRPF_2026)

    assert resultado.total_devengado == Decimal("1590.26")
    assert resultado.liquido_a_percibir > 0
    assert resultado.liquido_a_percibir < resultado.total_devengado
    # Coste empresa siempre mayor que el devengado (incluye cuotas empresa)
    assert resultado.coste_empresa_total > resultado.total_devengado


def test_prorrata_pagas_extra_no_prorrateadas_no_se_paga_pero_cotiza():
    convenio = convenio_metal_grupo5(pagas_extra_prorrateadas=False)
    eventos = EventosMes(periodo_anio=2026, periodo_mes=6, dias_naturales_periodo=30)
    resultado = calcular_nomina(convenio, eventos, parametros_2026(), TRAMOS_IRPF_2026)

    conceptos_devengo = [l.concepto for l in resultado.lineas if l.bloque == "devengo"]
    assert not any("Prorrata de pagas extraordinarias" in c for c in conceptos_devengo)
    # La base de cotización debe ser mayor que el salario base porque incluye
    # la prorrata de pagas extra aunque no se pague en efectivo (art. 109 LGSS)
    assert resultado.base_cotizacion_comun > resultado.total_devengado


def test_prorrata_pagas_extra_prorrateadas_se_paga():
    convenio = convenio_metal_grupo5(pagas_extra_prorrateadas=True)
    eventos = EventosMes(periodo_anio=2026, periodo_mes=6, dias_naturales_periodo=30)
    resultado = calcular_nomina(convenio, eventos, parametros_2026(), TRAMOS_IRPF_2026)

    salario_base = Decimal("1590.26")
    prorrata_esperada = (salario_base * 2 / 12).quantize(Decimal("0.01"))
    assert resultado.total_devengado == (salario_base + prorrata_esperada).quantize(Decimal("0.01"))


def test_horas_extra_aumentan_devengo():
    convenio = convenio_metal_grupo5()
    sin_horas = calcular_nomina(
        convenio, EventosMes(periodo_anio=2026, periodo_mes=6), parametros_2026(), TRAMOS_IRPF_2026
    )
    con_horas = calcular_nomina(
        convenio,
        EventosMes(periodo_anio=2026, periodo_mes=6, horas_extra=Decimal("10")),
        parametros_2026(),
        TRAMOS_IRPF_2026,
    )
    assert con_horas.total_devengado > sin_horas.total_devengado


def test_it_reduce_devengo_pero_genera_prestacion():
    convenio = convenio_metal_grupo5()
    resultado = calcular_nomina(
        convenio,
        EventosMes(periodo_anio=2026, periodo_mes=6, dias_naturales_periodo=30, dias_it=10),
        parametros_2026(),
        TRAMOS_IRPF_2026,
    )
    conceptos = [l.concepto for l in resultado.lineas]
    assert any("IT días 4-20" in c for c in conceptos)
    # 20 días trabajados de 30 -> salario prorrateado menor que el mes completo
    assert resultado.total_devengado < Decimal("1590.26") + Decimal("50")  # margen por prestación IT sumada
    # La prestación de IT no cotiza (art. 173 LGSS, simplificación del MVP)
    lineas_it = [l for l in resultado.lineas if "IT" in l.concepto]
    assert lineas_it and all(l.cotiza is False for l in lineas_it)


def test_vacaciones_no_reducen_devengo():
    """Los días de vacaciones se pagan igual que los trabajados (no son IT)."""
    convenio = convenio_metal_grupo5()
    resultado = calcular_nomina(
        convenio,
        EventosMes(periodo_anio=2026, periodo_mes=6, dias_naturales_periodo=30, dias_vacaciones=15),
        parametros_2026(),
        TRAMOS_IRPF_2026,
    )
    assert resultado.total_devengado == Decimal("1590.26")


def test_irpf_creciente_con_salario():
    convenio_bajo = convenio_metal_grupo5(salario_convenio_mensual=Decimal("1200"))
    convenio_alto = convenio_metal_grupo5(salario_convenio_mensual=Decimal("4000"))
    eventos = EventosMes(periodo_anio=2026, periodo_mes=6)

    resultado_bajo = calcular_nomina(convenio_bajo, eventos, parametros_2026(), TRAMOS_IRPF_2026)
    resultado_alto = calcular_nomina(convenio_alto, eventos, parametros_2026(), TRAMOS_IRPF_2026)

    irpf_bajo = next(l.importe for l in resultado_bajo.lineas if l.concepto == "Retención IRPF")
    irpf_alto = next(l.importe for l in resultado_alto.lineas if l.concepto == "Retención IRPF")
    tipo_bajo = irpf_bajo / resultado_bajo.base_sujeta_irpf
    tipo_alto = irpf_alto / resultado_alto.base_sujeta_irpf
    assert tipo_alto > tipo_bajo  # progresividad


def test_dietas_suman_al_liquido_pero_no_cotizan_ni_tributan():
    convenio = convenio_metal_grupo5()
    sin_dietas = calcular_nomina(
        convenio, EventosMes(periodo_anio=2026, periodo_mes=6), parametros_2026(), TRAMOS_IRPF_2026
    )
    con_dietas = calcular_nomina(
        convenio,
        EventosMes(
            periodo_anio=2026,
            periodo_mes=6,
            numero_medias_dietas=2,
            numero_dietas_completas_cortas=3,
        ),
        parametros_2026(),
        TRAMOS_IRPF_2026,
    )

    importe_dietas_esperado = (Decimal("12.14") * 2 + Decimal("59.17") * 3).quantize(Decimal("0.01"))
    assert con_dietas.total_dietas_exentas == importe_dietas_esperado
    assert con_dietas.total_devengado == sin_dietas.total_devengado + importe_dietas_esperado
    # Las dietas no deben alterar la base de cotización ni la de IRPF
    assert con_dietas.base_cotizacion_comun == sin_dietas.base_cotizacion_comun
    assert con_dietas.base_sujeta_irpf == sin_dietas.base_sujeta_irpf

    lineas_dieta = [l for l in con_dietas.lineas if "dieta" in l.concepto.lower()]
    assert lineas_dieta and all(l.cotiza is False for l in lineas_dieta)
    linea_salario = next(l for l in con_dietas.lineas if l.concepto == "Salario base convenio")
    assert linea_salario.cotiza is True
    # Pero sí incrementan el líquido a percibir
    assert con_dietas.liquido_a_percibir == sin_dietas.liquido_a_percibir + importe_dietas_esperado
