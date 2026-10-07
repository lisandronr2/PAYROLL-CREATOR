from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (registra todas las tablas)
from app.database import Base
from app.engine.repositorio import obtener_datos_convenio_contrato
from app.models.contrato import Contrato
from app.models.convenio import CategoriaProfesional, Convenio, ConvenioTablaSalarial
from app.models.empresa import Empresa
from app.models.trabajador import Trabajador
from app.seed.convenios import cargar_reglas_convenio_metal

NOMBRE_METAL = "Industria, Servicios e Instalaciones del Metal de Madrid"
PERIODO = date(2026, 10, 1)


@pytest.fixture()
def db():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(bind=motor)
    sesion = sessionmaker(bind=motor)()
    yield sesion
    sesion.close()


def crear_contrato(db, fecha_antiguedad, max_tramos, nombre_convenio="Convenio de prueba"):
    convenio = Convenio(
        nombre=nombre_convenio,
        numero_pagas=14,
        jornada_anual_horas=Decimal("1750"),
        antiguedad_max_tramos=max_tramos,
    )
    empresa = Empresa(razon_social="Empresa SL", cif="B00000001", tipo_at_ep_pct=Decimal("1.5"))
    db.add_all([convenio, empresa])
    db.flush()
    categoria = CategoriaProfesional(convenio_id=convenio.id, grupo="4", nombre="Empleado/a", grupo_cotizacion=4)
    trabajador = Trabajador(
        empresa_id=empresa.id, nombre="Ana", apellidos="Prueba", nif="11111111H", fecha_alta=fecha_antiguedad
    )
    db.add_all([categoria, trabajador])
    db.flush()
    db.add(
        ConvenioTablaSalarial(
            categoria_id=categoria.id,
            anio=2026,
            salario_convenio_anual=Decimal("23930.65"),
            salario_convenio_mensual=Decimal("1709.33"),
            valor_quinquenio_o_trienio=Decimal("33.38"),
            vigente_desde=date(2026, 1, 1),
        )
    )
    contrato = Contrato(
        trabajador_id=trabajador.id,
        convenio_id=convenio.id,
        categoria_id=categoria.id,
        tipo_contrato="indefinido",
        jornada_porcentaje=Decimal("100"),
        fecha_inicio=fecha_antiguedad,
        complemento_mensual=Decimal("0"),
        pagas_extra_prorrateadas=False,
    )
    db.add(contrato)
    db.commit()
    return contrato


def quinquenios(db, contrato):
    return obtener_datos_convenio_contrato(db, contrato, PERIODO).numero_quinquenios_o_trienios


def test_con_tope_de_cinco_quien_lleva_mas_de_25_anios_cobra_cinco(db):
    contrato = crear_contrato(db, date(1990, 1, 1), max_tramos=5)  # 36 años = 7 quinquenios sin tope
    assert quinquenios(db, contrato) == 5


def test_sin_tope_se_cuentan_todos_los_quinquenios(db):
    contrato = crear_contrato(db, date(1990, 1, 1), max_tramos=None)
    assert quinquenios(db, contrato) == 7


def test_por_debajo_del_tope_se_cuenta_uno_por_cada_cinco_anios(db):
    contrato = crear_contrato(db, date(2014, 1, 1), max_tramos=5)  # 12 años cumplidos
    assert quinquenios(db, contrato) == 2


def test_justo_en_el_tope(db):
    contrato = crear_contrato(db, date(2001, 1, 1), max_tramos=5)  # 25 años cumplidos
    assert quinquenios(db, contrato) == 5


def test_el_metal_recibe_el_tope_de_cinco_al_cargar_sus_reglas(db):
    metal = Convenio(nombre=NOMBRE_METAL, numero_pagas=14)
    db.add(metal)
    db.commit()

    cargar_reglas_convenio_metal(db)
    db.refresh(metal)

    assert metal.antiguedad_max_tramos == 5


def test_cargar_las_reglas_no_pisa_un_tope_cambiado_a_mano(db):
    metal = Convenio(nombre=NOMBRE_METAL, numero_pagas=14, antiguedad_max_tramos=6)
    db.add(metal)
    db.commit()

    cargar_reglas_convenio_metal(db)
    db.refresh(metal)

    assert metal.antiguedad_max_tramos == 6
