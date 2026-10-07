from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (registra todas las tablas)
from app.database import Base
from app.models.contrato import Contrato
from app.models.convenio import CategoriaProfesional, Convenio
from app.models.empresa import Empresa
from app.models.liquidacion import LiquidacionLinea
from app.models.trabajador import Trabajador
from app.pdf import generador_liquidacion
from app.routers import liquidaciones as router
from app.schemas.liquidacion import CalcularLiquidacionRequest
from app.seed.convenios import (
    cargar_reglas_convenio_metal,
    seed_convenio_dietas,
    seed_convenios,
    seed_subniveles_metal,
)
from app.seed.parametros_legales import corregir_parametros_legales, seed_parametros_legales
from app.seed.tabla_irpf import corregir_tabla_irpf, seed_tabla_irpf


@pytest.fixture()
def db():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(bind=motor)
    sesion = sessionmaker(bind=motor)()
    seed_parametros_legales(sesion)
    corregir_parametros_legales(sesion)
    seed_tabla_irpf(sesion)
    corregir_tabla_irpf(sesion)
    seed_convenios(sesion)
    seed_convenio_dietas(sesion)
    seed_subniveles_metal(sesion)
    cargar_reglas_convenio_metal(sesion)
    yield sesion
    sesion.close()


@pytest.fixture()
def contrato(db):
    metal = db.query(Convenio).filter(Convenio.nombre.like("Industria, Servicios%")).first()
    categoria = (
        db.query(CategoriaProfesional)
        .filter(CategoriaProfesional.convenio_id == metal.id, CategoriaProfesional.grupo == "4")
        .first()
    )
    empresa = Empresa(razon_social="Soluciones Mata SL", cif="B00000001", direccion="Calle Mayor 12, Madrid")
    db.add(empresa)
    db.flush()
    trabajador = Trabajador(
        empresa_id=empresa.id,
        nombre="Ana",
        apellidos="Prueba Lopez",
        nif="12345678Z",
        fecha_alta=date(2018, 3, 15),
        fecha_nacimiento=date(1985, 5, 5),
    )
    db.add(trabajador)
    db.flush()
    contrato = Contrato(
        trabajador_id=trabajador.id,
        convenio_id=metal.id,
        categoria_id=categoria.id,
        tipo_contrato="indefinido",
        jornada_porcentaje=Decimal("100"),
        fecha_inicio=date(2018, 3, 15),
        complemento_mensual=Decimal("0"),
        pagas_extra_prorrateadas=False,
    )
    db.add(contrato)
    db.commit()
    return contrato


def peticion(contrato, **cambios):
    datos = dict(
        contrato_id=contrato.id,
        fecha_baja=date(2026, 10, 31),
        motivo="dimision",
        vacaciones_disfrutadas=Decimal("15"),
        unidad_vacaciones="laborables",
        dias_preaviso_trabajados=0,
        notas="Prueba",
    )
    datos.update(cambios)
    return CalcularLiquidacionRequest(**datos)


def test_guardar_conserva_los_datos_y_el_resultado_calculado(db, contrato):
    payload = peticion(contrato)
    vista_previa = router.calcular(payload, db)

    guardada = router.crear_liquidacion(payload, db)

    assert guardada.id is not None
    assert guardada.trabajador_nombre == "Ana Prueba Lopez"
    assert guardada.motivo == "dimision"
    assert guardada.notas == "Prueba"
    assert guardada.dias_preaviso_exigidos == 15  # sugerido por el convenio (resto del personal)
    assert guardada.liquido_a_percibir == vista_previa.liquido_a_percibir
    assert [(l.concepto, l.importe) for l in guardada.lineas] == [
        (l.concepto, l.importe) for l in vista_previa.lineas
    ]
    assert guardada.avisos == vista_previa.avisos


def test_listar_y_obtener(db, contrato):
    primera = router.crear_liquidacion(peticion(contrato), db)
    segunda = router.crear_liquidacion(peticion(contrato, motivo="despido_objetivo"), db)

    assert {l.id for l in router.listar_liquidaciones(db)} == {primera.id, segunda.id}
    assert router.obtener_liquidacion(segunda.id, db).motivo == "despido_objetivo"


def test_editar_recalcula_y_sustituye_las_lineas(db, contrato):
    guardada = router.crear_liquidacion(peticion(contrato), db)
    assert guardada.indemnizacion_legal == 0

    editada = router.actualizar_liquidacion(
        guardada.id, peticion(contrato, motivo="despido_improcedente", dias_preaviso_trabajados=0), db
    )

    assert editada.id == guardada.id
    assert editada.motivo == "despido_improcedente"
    assert editada.indemnizacion_legal > 0
    assert any(l.bloque == "indemnizacion" for l in editada.lineas)
    # Las líneas antiguas no se acumulan: solo quedan las del nuevo cálculo.
    nuevas = router.calcular(peticion(contrato, motivo="despido_improcedente"), db)
    assert len(editada.lineas) == len(nuevas.lineas)
    assert db.query(LiquidacionLinea).filter(LiquidacionLinea.liquidacion_id == guardada.id).count() == len(
        nuevas.lineas
    )


def test_editar_una_liquidacion_inexistente_da_404(db, contrato):
    with pytest.raises(HTTPException) as error:
        router.actualizar_liquidacion(999, peticion(contrato), db)
    assert error.value.status_code == 404


def test_borrar_elimina_la_liquidacion_y_sus_lineas(db, contrato):
    guardada = router.crear_liquidacion(peticion(contrato), db)
    identificador = guardada.id

    router.eliminar_liquidacion(identificador, db)

    with pytest.raises(HTTPException) as error:
        router.obtener_liquidacion(identificador, db)
    assert error.value.status_code == 404
    assert db.query(LiquidacionLinea).filter(LiquidacionLinea.liquidacion_id == identificador).count() == 0


@pytest.mark.parametrize("tipo", ["trabajador", "interno"])
def test_pdf_se_genera_en_ambas_versiones(db, contrato, tmp_path, monkeypatch, tipo):
    monkeypatch.setattr(generador_liquidacion, "OUTPUT_DIR", str(tmp_path))
    guardada = router.crear_liquidacion(peticion(contrato, motivo="despido_improcedente"), db)

    respuesta = router.pdf_liquidacion(guardada.id, tipo, db)

    contenido = open(respuesta.path, "rb").read()
    assert contenido.startswith(b"%PDF")
    assert respuesta.media_type == "application/pdf"
    assert respuesta.filename == f"liquidacion_{guardada.id}_{tipo}.pdf"


def test_pdf_con_tipo_no_valido_da_422(db, contrato):
    guardada = router.crear_liquidacion(peticion(contrato), db)
    with pytest.raises(HTTPException) as error:
        router.pdf_liquidacion(guardada.id, "otro", db)
    assert error.value.status_code == 422


def test_fecha_de_baja_anterior_al_ingreso_da_422_y_no_guarda(db, contrato):
    with pytest.raises(HTTPException) as error:
        router.crear_liquidacion(peticion(contrato, fecha_baja=date(2018, 1, 1)), db)
    assert error.value.status_code == 422
    assert router.listar_liquidaciones(db) == []


def test_el_pdf_de_la_liquidacion_lleva_el_logo_de_la_empresa(db, contrato, tmp_path, monkeypatch):
    from pypdf import PdfReader

    monkeypatch.setattr(generador_liquidacion, "OUTPUT_DIR", str(tmp_path))
    guardada = router.crear_liquidacion(peticion(contrato), db)

    ruta = router.pdf_liquidacion(guardada.id, "trabajador", db).path

    assert sum(len(pagina.images) for pagina in PdfReader(ruta).pages) >= 1
