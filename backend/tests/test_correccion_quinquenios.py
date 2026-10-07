from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (registra todas las tablas)
from app.database import Base
from app.models.convenio import CategoriaProfesional, Convenio, ConvenioTablaSalarial
from app.seed.convenios import corregir_quinquenios_metal

NOMBRE_METAL = "Industria, Servicios e Instalaciones del Metal de Madrid"


@pytest.fixture()
def db():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(bind=motor)
    sesion = sessionmaker(bind=motor)()
    yield sesion
    sesion.close()


def crear_categoria(db, convenio, grupo, quinquenio):
    categoria = CategoriaProfesional(convenio_id=convenio.id, grupo=grupo, nombre=f"Cat {grupo}", grupo_cotizacion=4)
    db.add(categoria)
    db.flush()
    tabla = ConvenioTablaSalarial(
        categoria_id=categoria.id,
        anio=2026,
        salario_convenio_anual=Decimal("23930.65"),
        salario_convenio_mensual=Decimal("1709.33"),
        valor_quinquenio_o_trienio=Decimal(quinquenio),
        vigente_desde=date(2026, 1, 1),
    )
    db.add(tabla)
    db.commit()
    return tabla


def convenio_metal(db):
    convenio = Convenio(nombre=NOMBRE_METAL, numero_pagas=14)
    db.add(convenio)
    db.flush()
    return convenio


def test_sustituye_el_valor_erroneo_del_grupo_y_de_sus_subniveles(db):
    convenio = convenio_metal(db)
    grupo4 = crear_categoria(db, convenio, "4", "841.22")
    subnivel = crear_categoria(db, convenio, "4.3", "841.22")
    grupo5 = crear_categoria(db, convenio, "5", "26.46")

    corregir_quinquenios_metal(db)
    db.refresh(grupo4)
    db.refresh(subnivel)
    db.refresh(grupo5)

    assert grupo4.valor_quinquenio_o_trienio == Decimal("33.37")
    assert subnivel.valor_quinquenio_o_trienio == Decimal("33.37")
    assert grupo5.valor_quinquenio_o_trienio == Decimal("31.91")


def test_corrige_la_estimacion_del_grupo_4_ya_aplicada_en_produccion(db):
    # Con el build 2764 se aplicó 33,38 (estimado); la tabla oficial dice 33,37.
    convenio = convenio_metal(db)
    grupo4 = crear_categoria(db, convenio, "4", "33.38")
    subnivel = crear_categoria(db, convenio, "4.7", "33.38")

    corregir_quinquenios_metal(db)
    db.refresh(grupo4)
    db.refresh(subnivel)

    assert grupo4.valor_quinquenio_o_trienio == Decimal("33.37")
    assert subnivel.valor_quinquenio_o_trienio == Decimal("33.37")


def test_los_valores_oficiales_ya_correctos_no_cambian(db):
    convenio = convenio_metal(db)
    tablas = {g: crear_categoria(db, convenio, g, v) for g, v in
              {"1": "42.72", "2": "38.88", "3": "35.78", "5": "31.91", "6": "31.19", "7": "30.82"}.items()}

    corregir_quinquenios_metal(db)

    for grupo, tabla in tablas.items():
        db.refresh(tabla)
    assert {g: str(t.valor_quinquenio_o_trienio) for g, t in tablas.items()} == {
        "1": "42.72", "2": "38.88", "3": "35.78", "5": "31.91", "6": "31.19", "7": "30.82"
    }


def test_no_pisa_un_valor_corregido_a_mano(db):
    convenio = convenio_metal(db)
    tabla = crear_categoria(db, convenio, "4", "34.00")  # valor oficial puesto por el usuario

    corregir_quinquenios_metal(db)
    db.refresh(tabla)

    assert tabla.valor_quinquenio_o_trienio == Decimal("34.00")


def test_es_idempotente(db):
    convenio = convenio_metal(db)
    tabla = crear_categoria(db, convenio, "1", "1130.84")

    corregir_quinquenios_metal(db)
    corregir_quinquenios_metal(db)
    db.refresh(tabla)

    assert tabla.valor_quinquenio_o_trienio == Decimal("42.72")


def test_no_toca_otros_convenios(db):
    otro = Convenio(nombre="Comercio (Madrid) — EJEMPLO", numero_pagas=14)
    db.add(otro)
    db.flush()
    tabla = crear_categoria(db, otro, "4", "841.22")

    corregir_quinquenios_metal(db)
    db.refresh(tabla)

    assert tabla.valor_quinquenio_o_trienio == Decimal("841.22")


def test_sin_convenio_metal_no_hace_nada(db):
    corregir_quinquenios_metal(db)  # no debe fallar
