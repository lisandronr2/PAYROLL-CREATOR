from datetime import date
from decimal import Decimal

import pytest

from app.engine.finiquito import (
    EntradaLiquidacion,
    anios_de_servicio,
    calcular_indemnizacion,
    calcular_liquidacion,
    calcular_vacaciones,
    pagas_extra_pendientes,
)
from app.engine.tipos import DatosConvenioContrato
from tests.test_calculo import TRAMOS_IRPF_2026, parametros_2026


def convenio_prueba(**cambios):
    datos = dict(
        nombre_convenio="Convenio de prueba",
        numero_pagas=14,
        jornada_anual_horas=Decimal("1750"),
        salario_convenio_mensual=Decimal("1500"),
        base_calculo_complementos_mensual=Decimal("1500"),
        valor_quinquenio_o_trienio=Decimal("0"),
        plus_convenio_mensual=Decimal("0"),
        jornada_porcentaje=Decimal("100"),
        tipo_contrato="indefinido",
        pagas_extra_prorrateadas=False,
        numero_quinquenios_o_trienios=0,
        grupo_cotizacion=5,
        tipo_at_ep_pct=Decimal("1.5"),
    )
    datos.update(cambios)
    return DatosConvenioContrato(**datos)


def entrada(**cambios):
    datos = dict(
        convenio=convenio_prueba(),
        parametros=parametros_2026(),
        tramos_irpf=TRAMOS_IRPF_2026,
        fecha_ingreso=date(2020, 1, 1),
        fecha_baja=date(2025, 12, 31),
        motivo="dimision",
    )
    datos.update(cambios)
    return EntradaLiquidacion(**datos)


# ---------- antigüedad ----------

def test_anios_de_servicio_exactos_y_fracciones():
    assert anios_de_servicio(date(2020, 1, 1), date(2026, 1, 1)) == Decimal(6)
    # 6 meses exactos = medio año
    assert anios_de_servicio(date(2025, 1, 1), date(2025, 7, 1)) == Decimal("0.5")
    assert anios_de_servicio(date(2026, 1, 1), date(2025, 1, 1)) == Decimal(0)


# ---------- indemnización ----------

def test_improcedente_posterior_a_2012_son_33_dias_por_anio():
    ind = calcular_indemnizacion("despido_improcedente", date(2020, 1, 1), date(2025, 12, 31), Decimal("100"))
    assert ind.dias == Decimal(198)
    assert ind.importe == Decimal("19800.00")


def test_improcedente_con_tramo_anterior_a_2012_son_45_dias_por_anio():
    # 2 años a 45 días (hasta 11/02/2012) + 1 año a 33 días
    ind = calcular_indemnizacion("despido_improcedente", date(2010, 2, 12), date(2013, 2, 11), Decimal("100"))
    assert ind.dias == Decimal(123)
    assert ind.importe == Decimal("12300.00")


def test_improcedente_tope_de_24_mensualidades():
    ind = calcular_indemnizacion("despido_improcedente", date(2012, 2, 12), date(2037, 2, 11), Decimal("100"))
    assert ind.dias == Decimal(720)
    assert ind.importe == Decimal("72000.00")


def test_improcedente_si_el_tramo_antiguo_supera_720_dias_ese_es_el_tope():
    # 22 años a 45 días = 990 días (> 720): el tope pasa a ser 990, no 1.023
    ind = calcular_indemnizacion("despido_improcedente", date(1990, 2, 12), date(2013, 2, 11), Decimal("100"))
    assert ind.dias == Decimal(990)


def test_improcedente_nunca_supera_42_mensualidades():
    ind = calcular_indemnizacion("despido_improcedente", date(1982, 2, 12), date(2013, 2, 11), Decimal("100"))
    assert ind.dias == Decimal(1260)


def test_objetivo_son_20_dias_por_anio_con_tope_de_12_mensualidades():
    ind = calcular_indemnizacion("despido_objetivo", date(2020, 1, 1), date(2025, 12, 31), Decimal("100"))
    assert ind.dias == Decimal(120)
    topada = calcular_indemnizacion("despido_objetivo", date(2000, 1, 1), date(2025, 12, 31), Decimal("100"))
    assert topada.dias == Decimal(360)


def test_fin_de_temporal_son_12_dias_por_anio():
    ind = calcular_indemnizacion("fin_contrato_temporal", date(2024, 1, 1), date(2025, 12, 31), Decimal("100"))
    assert ind.dias == Decimal(24)
    assert ind.importe == Decimal("2400.00")


@pytest.mark.parametrize("motivo", ["dimision", "despido_disciplinario", "mutuo_acuerdo", "fin_periodo_prueba"])
def test_motivos_sin_indemnizacion_legal(motivo):
    assert calcular_indemnizacion(motivo, date(2020, 1, 1), date(2025, 12, 31), Decimal("100")) is None


# ---------- vacaciones ----------

def test_vacaciones_devengadas_menos_disfrutadas_en_laborables():
    # 182 de 365 días de servicio: 30 × 182/365 = 14,96 naturales devengados.
    # 5 laborables con 22 laborables = 30 naturales: 5 × 30/22 = 6,82 naturales.
    devengadas, disfrutadas, anteriores, pendientes = calcular_vacaciones(
        date(2020, 1, 1), date(2025, 7, 1), 30, 22, Decimal("5"), "laborables", Decimal("0")
    )
    assert devengadas == Decimal("14.96")
    assert disfrutadas == Decimal("6.82")
    assert anteriores == Decimal("0.00")
    assert pendientes == Decimal("8.14")


def test_vacaciones_en_laborables_exigen_que_el_convenio_las_defina():
    with pytest.raises(ValueError):
        calcular_vacaciones(date(2020, 1, 1), date(2025, 7, 1), 30, None, Decimal("5"), "laborables", Decimal("0"))


def test_vacaciones_si_ingreso_en_el_mismo_anio_se_devenga_desde_el_ingreso():
    devengadas, *_ = calcular_vacaciones(
        date(2025, 7, 1), date(2025, 12, 31), 30, None, Decimal("0"), "naturales", Decimal("0")
    )
    assert devengadas == Decimal("15.12")  # 184 de 365 días


# ---------- pagas extraordinarias ----------

def test_paga_de_julio_proporcional_si_la_baja_es_en_el_primer_semestre():
    items, avisos = pagas_extra_pendientes(date(2020, 1, 1), date(2025, 3, 31), 14, Decimal("1500"), False)
    assert len(items) == 1
    assert "julio" in items[0][0]
    assert items[0][1] == Decimal("745.86")  # 1.500 × 90/181
    assert avisos == []


def test_baja_justo_antes_del_abono_de_julio_cobra_la_paga_entera_y_parte_de_la_de_diciembre():
    items, _ = pagas_extra_pendientes(date(2020, 1, 1), date(2025, 7, 10), 14, Decimal("1500"), False)
    importes = {nombre.split()[3]: importe for nombre, importe, _ in items}
    assert importes["julio"] == Decimal("1500.00")
    assert importes["diciembre"] == Decimal("81.52")  # 1.500 × 10/184


def test_baja_tras_el_abono_de_diciembre_no_deja_pagas_pendientes():
    items, _ = pagas_extra_pendientes(date(2020, 1, 1), date(2025, 12, 31), 14, Decimal("1500"), False)
    assert items == []


def test_pagas_prorrateadas_no_generan_nada_pendiente():
    assert pagas_extra_pendientes(date(2020, 1, 1), date(2025, 3, 31), 14, Decimal("1500"), True) == ([], [])


def test_otro_numero_de_pagas_avisa_del_supuesto():
    items, avisos = pagas_extra_pendientes(date(2020, 1, 1), date(2025, 6, 30), 15, Decimal("1500"), False)
    assert len(items) == 1
    assert avisos


# ---------- liquidación completa ----------

def lineas_por_texto(resultado, texto):
    return [l for l in resultado.lineas if texto.lower() in l.concepto.lower()]


def test_dimision_sin_preaviso_descuenta_los_dias_omitidos():
    # Mensual 1.500 + prorrata de 2 pagas (1.500 × 2/12 = 250) = 1.750 → 58,3333 €/día × 15 = 875
    r = calcular_liquidacion(entrada(motivo="dimision", dias_preaviso_exigidos=15, dias_preaviso_trabajados=0))
    descuento = lineas_por_texto(r, "preaviso incumplido")
    assert len(descuento) == 1
    assert descuento[0].bloque == "descuento"
    assert descuento[0].importe == Decimal("875.00")
    assert r.indemnizacion_legal == Decimal("0")


def test_dimision_con_el_preaviso_cumplido_no_descuenta():
    r = calcular_liquidacion(entrada(motivo="dimision", dias_preaviso_exigidos=15, dias_preaviso_trabajados=15))
    assert lineas_por_texto(r, "preaviso") == []


def test_despido_objetivo_sin_preaviso_la_empresa_paga_los_dias_y_cotizan():
    r = calcular_liquidacion(entrada(motivo="despido_objetivo", dias_preaviso_exigidos=15, dias_preaviso_trabajados=0))
    compensacion = lineas_por_texto(r, "compensación por preaviso")
    assert len(compensacion) == 1
    assert compensacion[0].importe == Decimal("875.00")
    assert compensacion[0].cotiza and compensacion[0].tributa


def test_la_indemnizacion_legal_no_cotiza_ni_tributa():
    r = calcular_liquidacion(entrada(motivo="despido_improcedente", dias_preaviso_exigidos=0))
    indemnizacion = lineas_por_texto(r, "indemnización por")
    assert len(indemnizacion) == 1
    assert indemnizacion[0].importe == r.indemnizacion_legal > 0
    assert not indemnizacion[0].cotiza and not indemnizacion[0].tributa
    # Las bases solo recogen el salario, no la indemnización
    assert r.base_cotizacion == r.base_irpf
    assert r.total_ingresos == sum(
        l.importe for l in r.lineas if l.bloque in ("devengo", "indemnizacion")
    )


def test_los_totales_cuadran():
    r = calcular_liquidacion(
        entrada(
            motivo="despido_objetivo",
            fecha_baja=date(2025, 5, 20),
            vacaciones_disfrutadas=Decimal("3"),
            unidad_vacaciones="naturales",
            dias_preaviso_exigidos=15,
            dias_preaviso_trabajados=5,
            otras_cantidades=Decimal("100"),
            descuentos=Decimal("50"),
        )
    )
    assert r.total_deducciones == r.cotizacion_trabajador + r.retencion_irpf + r.total_descuentos
    assert r.liquido_a_percibir == r.total_ingresos - r.total_deducciones
    assert r.coste_empresa_total == r.total_ingresos - r.total_descuentos + r.cuota_empresa_ss
    assert r.total_descuentos >= Decimal("50")


def test_vacaciones_disfrutadas_de_mas_se_descuentan():
    r = calcular_liquidacion(
        entrada(fecha_baja=date(2025, 1, 31), vacaciones_disfrutadas=Decimal("20"), unidad_vacaciones="naturales")
    )
    exceso = lineas_por_texto(r, "disfrutadas en exceso")
    assert len(exceso) == 1
    assert exceso[0].bloque == "descuento"
    assert any("exceso" in aviso for aviso in r.avisos)


def test_salario_del_mes_de_baja_es_proporcional_a_los_dias_trabajados():
    r = calcular_liquidacion(entrada(fecha_baja=date(2025, 6, 15), unidad_vacaciones="naturales"))
    salario = lineas_por_texto(r, "salario base")
    assert salario[0].importe == Decimal("750.00")  # 1.500 × 15/30


def test_fecha_de_baja_anterior_al_ingreso_es_un_error():
    with pytest.raises(ValueError):
        calcular_liquidacion(entrada(fecha_ingreso=date(2025, 6, 1), fecha_baja=date(2025, 5, 1)))


def test_motivo_desconocido_es_un_error():
    with pytest.raises(ValueError):
        calcular_liquidacion(entrada(motivo="inventado"))
