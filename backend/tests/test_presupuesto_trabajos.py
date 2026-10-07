from datetime import date
from decimal import Decimal

import pytest
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (registra todas las tablas)
from app.database import Base
from app.engine.presupuesto import calcular_totales_presupuesto
from app.models.convenio import CategoriaProfesional, Convenio
from app.models.empresa import Empresa
from app.models.presupuesto import PresupuestoLineaTrabajo
from app.pdf import generador_presupuesto
from app.routers import presupuestos as router
from app.schemas.presupuesto import (
    PresupuestoCreate,
    PresupuestoLineaOtroCosteCreate,
    PresupuestoLineaPersonalCreate,
    PresupuestoLineaTrabajoCreate,
)
from app.seed.convenios import seed_convenio_dietas, seed_convenios
from app.seed.parametros_negocio import seed_parametros_negocio

D = Decimal


# ---------- motor ----------

def test_los_trabajos_suman_al_coste_directo_y_les_aplican_gastos_y_margen():
    r = calcular_totales_presupuesto(
        coste_directo_mano_obra=D("1600"),
        coste_directo_dietas=D("0"),
        coste_directo_hotel=D("0"),
        coste_directo_combustible=D("0"),
        coste_directo_trabajos=D("750"),
        coste_directo_materiales=D("150"),
        gastos_generales_pct=D("15"),
        margen_beneficio_pct=D("6"),
        iva_pct=D("21"),
    )
    assert r.coste_directo_trabajos == D("750.00")
    assert r.coste_directo_total == D("2500.00")
    assert r.gastos_generales_importe == D("375.00")
    assert r.margen_importe == D("172.50")
    assert r.precio_venta == D("3047.50")
    assert r.iva_importe == D("639.98")
    assert r.precio_total_cliente == D("3687.48")


# ---------- guardado y PDF ----------

@pytest.fixture()
def db():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(bind=motor)
    sesion = sessionmaker(bind=motor)()
    seed_convenios(sesion)
    seed_convenio_dietas(sesion)
    seed_parametros_negocio(sesion)
    sesion.add(Empresa(razon_social="Soluciones Mata SL", cif="B00000001", direccion="Calle Mayor 12, Madrid"))
    sesion.commit()
    yield sesion
    sesion.close()


def peticion(db, trabajos=None, otros=True, **cambios):
    metal = db.query(Convenio).filter(Convenio.nombre.like("Industria, Servicios%")).first()
    categoria = (
        db.query(CategoriaProfesional)
        .filter(CategoriaProfesional.convenio_id == metal.id, CategoriaProfesional.grupo == "4")
        .first()
    )
    datos = dict(
        empresa_id=db.query(Empresa).first().id,
        convenio_id=metal.id,
        nombre="Instalación nave 4",
        cliente_nombre="Cliente SL",
        fecha=date(2026, 10, 7),
        lineas_personal=[
            PresupuestoLineaPersonalCreate(
                categoria_id=categoria.id, cantidad_personas=2, precio_hora=D("20"), dias_dedicacion=D("5")
            )
        ],
        lineas_trabajos=trabajos
        if trabajos is not None
        else [
            PresupuestoLineaTrabajoCreate(concepto="Montaje de estructura", cantidad=D("2"), precio_unitario=D("300")),
            PresupuestoLineaTrabajoCreate(concepto="Pintura y acabados", cantidad=D("1"), precio_unitario=D("150")),
        ],
        lineas_otros=[PresupuestoLineaOtroCosteCreate(concepto="Tornillería", cantidad=D("3"), precio_unitario=D("50"))]
        if otros
        else [],
    )
    datos.update(cambios)
    return PresupuestoCreate(**datos)


def texto_pdf(ruta):
    return "\n".join(pagina.extract_text() for pagina in PdfReader(ruta).pages)


def test_guardar_con_trabajos_calcula_los_totales_y_conserva_las_lineas(db):
    p = router.crear_presupuesto(peticion(db), db)

    assert [(l.concepto, l.cantidad, l.importe) for l in p.lineas_trabajos] == [
        ("Montaje de estructura", D("2.00"), D("600.00")),
        ("Pintura y acabados", D("1.00"), D("150.00")),
    ]
    assert p.coste_directo_trabajos == D("750.00")
    assert p.coste_directo_mano_obra == D("1600.00")
    assert p.coste_directo_otros == D("150.00")
    assert p.coste_directo_total == D("2500.00")
    assert p.precio_venta == D("3047.50")
    assert p.precio_total_cliente == D("3687.48")


def test_un_presupuesto_sin_trabajos_se_calcula_como_antes(db):
    p = router.crear_presupuesto(peticion(db, trabajos=[]), db)

    assert p.lineas_trabajos == []
    assert p.coste_directo_trabajos == D("0.00")
    assert p.coste_directo_total == D("1750.00")  # 1.600 de personal + 150 de materiales


def test_editar_sustituye_los_trabajos_y_recalcula(db):
    p = router.crear_presupuesto(peticion(db), db)

    editado = router.actualizar_presupuesto(
        p.id,
        peticion(db, trabajos=[PresupuestoLineaTrabajoCreate(concepto="Solo uno", cantidad=D("1"), precio_unitario=D("400"))]),
        db,
    )

    assert [l.concepto for l in editado.lineas_trabajos] == ["Solo uno"]
    assert editado.coste_directo_trabajos == D("400.00")
    assert editado.coste_directo_total == D("2150.00")
    assert db.query(PresupuestoLineaTrabajo).filter(PresupuestoLineaTrabajo.presupuesto_id == p.id).count() == 1


def test_borrar_el_presupuesto_borra_sus_trabajos(db):
    p = router.crear_presupuesto(peticion(db), db)
    router.eliminar_presupuesto(p.id, db)
    assert db.query(PresupuestoLineaTrabajo).count() == 0


def test_pdf_cliente_muestra_los_trabajos_a_precio_de_venta_y_antes_de_los_materiales(db, tmp_path, monkeypatch):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db), db)

    texto = texto_pdf(router.descargar_pdf_presupuesto(p.id, "cliente", "clasico", db).path)

    assert "Trabajos a realizar" in texto
    assert "Montaje de estructura" in texto
    assert texto.index("Trabajos a realizar") < texto.index("Materiales y otros costes")
    # 750 € de coste × 1,219 (gastos generales y margen) = 914,25 € de venta
    assert "914.25" in texto
    assert "750.00" not in texto  # el cliente no ve el coste


def test_pdf_interno_muestra_el_coste_de_los_trabajos(db, tmp_path, monkeypatch):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db), db)

    texto = texto_pdf(router.descargar_pdf_presupuesto(p.id, "interno", "clasico", db).path)

    assert "Trabajos a realizar" in texto
    assert "Total trabajos a realizar" in texto
    assert "750.00" in texto


@pytest.mark.parametrize("tipo", ["cliente", "interno"])
def test_sin_trabajos_no_aparece_la_seccion(db, tmp_path, monkeypatch, tipo):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db, trabajos=[]), db)

    texto = texto_pdf(router.descargar_pdf_presupuesto(p.id, tipo, "clasico", db).path)

    assert "Trabajos a realizar" not in texto
    assert "Materiales y otros costes" in texto


# ---------- PDF profesional para el cliente ----------

from fastapi import HTTPException  # noqa: E402

from app.pdf.presupuesto_cliente import cant, eur, preparar_datos_cliente, repartir_redondeando  # noqa: E402


def test_repartir_redondeando_suma_exactamente_el_total():
    reparto = repartir_redondeando([D("1"), D("1"), D("1")], D("1.00"))
    assert sorted(reparto, reverse=True) == [D("0.34"), D("0.33"), D("0.33")]
    assert sum(reparto) == D("1.00")

    reparto = repartir_redondeando([D("1600"), D("150"), D("750")], D("3047.50"))
    assert sum(reparto) == D("3047.50")
    assert reparto[0] > reparto[2] > reparto[1]  # proporcional al coste


def test_repartir_redondeando_casos_limite():
    assert repartir_redondeando([], D("10")) == []
    assert repartir_redondeando([D("0"), D("0")], D("0")) == [D("0.00"), D("0.00")]


def test_formato_espanol_de_importes_y_cantidades():
    assert eur(D("1234.5")) == "1.234,50 €"
    assert eur(D("0")) == "0,00 €"
    assert eur(D("1234567.891")) == "1.234.567,89 €"
    assert cant(D("2.00")) == "2"
    assert cant(D("12.50")) == "12,5"
    assert cant(D("0.25")) == "0,25"
    assert cant(D("1200")) == "1.200"


def test_los_importes_del_cliente_suman_linea_a_linea_hasta_el_total(db):
    from app.models.presupuesto import Presupuesto

    p = router.crear_presupuesto(
        peticion(
            db,
            gasto_hotel=D("320"),
            gasto_combustible=D("150"),
            lineas_otros=[
                PresupuestoLineaOtroCosteCreate(concepto="Perfiles", cantidad=D("12.5"), precio_unitario=D("38.40")),
                PresupuestoLineaOtroCosteCreate(concepto="Tornillería", cantidad=D("7"), precio_unitario=D("3.33")),
            ],
        ),
        db,
    )
    datos = preparar_datos_cliente(db.get(Presupuesto, p.id))

    for seccion in datos.secciones:
        assert sum(l.importe for l in seccion.lineas) == seccion.total
    assert sum(s.total for s in datos.secciones) == datos.total_sin_iva == p.precio_venta
    assert datos.numero == f"2026-{p.id:04d}"
    assert datos.valido_hasta == "22/10/2026"


def test_pdf_profesional_tiene_el_contenido_de_un_presupuesto_para_cliente(db, tmp_path, monkeypatch):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db, notas="Acceso a la nave a cargo del cliente."), db)

    respuesta = router.descargar_pdf_presupuesto(p.id, "cliente", "profesional", db)
    texto = texto_pdf(respuesta.path)

    assert respuesta.filename == f"presupuesto_{p.id}_cliente.pdf"
    for esperado in (
        "PRESUPUESTO",
        f"2026-{p.id:04d}",
        "Válido hasta",
        "Soluciones Mata SL",
        "Cliente SL",
        "Trabajos a realizar",
        "Montaje de estructura",
        "TOTAL PRESUPUESTO",
        "IVA (21 %)",
        "Conforme del cliente",
        "Acceso a la nave a cargo del cliente.",
        "Página 1 de",
    ):
        assert esperado in texto, esperado
    assert texto.index("Trabajos a realizar") < texto.index("Materiales y otros costes")
    # Formato español y total exacto.
    assert "3.047,50 €" in texto
    # El cliente no ve costes ni el precio/hora interno.
    assert "750,00" not in texto
    assert "20,00 €" not in texto
    assert "PRECIO" not in texto.upper().replace("PRESUPUESTO", "")


def test_pdf_profesional_no_muestra_secciones_vacias(db, tmp_path, monkeypatch):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db, trabajos=[], otros=False), db)

    texto = texto_pdf(router.descargar_pdf_presupuesto(p.id, "cliente", "profesional", db).path)

    assert "Mano de obra" in texto
    for oculta in ("Trabajos a realizar", "Materiales y otros costes", "Hotel y combustible", "Dietas y desplazamiento"):
        assert oculta not in texto


def test_el_formato_solo_afecta_al_pdf_del_cliente_y_el_clasico_sigue_siendo_el_de_antes(db, tmp_path, monkeypatch):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db), db)

    clasico = router.descargar_pdf_presupuesto(p.id, "cliente", "clasico", db)
    interno = router.descargar_pdf_presupuesto(p.id, "interno", "profesional", db)

    assert clasico.filename == f"presupuesto_{p.id}_cliente_clasico.pdf"
    assert "Conforme del cliente" not in texto_pdf(clasico.path)
    assert interno.filename == f"presupuesto_{p.id}_interno.pdf"  # el interno ignora el formato
    assert "USO INTERNO" in texto_pdf(interno.path)


def test_formato_no_valido_da_422(db):
    p = router.crear_presupuesto(peticion(db), db)
    with pytest.raises(HTTPException) as error:
        router.descargar_pdf_presupuesto(p.id, "cliente", "otro", db)
    assert error.value.status_code == 422


# ---------- logo de la empresa en los PDF ----------

from app.pdf.logos import logo_de_empresa  # noqa: E402


def imagenes_pdf(ruta):
    return sum(len(pagina.images) for pagina in PdfReader(ruta).pages)


def test_el_logo_se_asigna_por_el_nombre_de_la_empresa():
    assert logo_de_empresa(Empresa(razon_social="SOLUCIONES MATA SL")).startswith("data:image/png;base64,")
    assert logo_de_empresa(Empresa(razon_social="Soluciones Mata, S.L.")) is not None
    assert logo_de_empresa(Empresa(razon_social="Otra Empresa SL")) is None


@pytest.mark.parametrize(
    "tipo,formato", [("cliente", "clasico"), ("cliente", "profesional"), ("interno", "clasico")]
)
def test_los_pdf_de_presupuesto_llevan_el_logo_de_su_empresa(db, tmp_path, monkeypatch, tipo, formato):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db), db)

    ruta = router.descargar_pdf_presupuesto(p.id, tipo, formato, db).path

    assert imagenes_pdf(ruta) >= 1


@pytest.mark.parametrize("tipo,formato", [("cliente", "clasico"), ("cliente", "profesional")])
def test_una_empresa_sin_logo_sale_solo_con_su_nombre(db, tmp_path, monkeypatch, tipo, formato):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    db.query(Empresa).first().razon_social = "Otra Empresa SL"
    db.commit()
    p = router.crear_presupuesto(peticion(db), db)

    ruta = router.descargar_pdf_presupuesto(p.id, tipo, formato, db).path

    assert imagenes_pdf(ruta) == 0
    assert "Otra Empresa SL" in texto_pdf(ruta)


# ---------- IVA en el formato profesional y presupuesto por items ----------
def test_pdf_profesional_con_iva_muestra_base_iva_y_total(db, tmp_path, monkeypatch):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db), db)

    texto = texto_pdf(router.descargar_pdf_presupuesto(p.id, "cliente", "profesional", db).path)

    assert "Base imponible" in texto and "IVA (21 %)" in texto
    assert eur(p.iva_importe) in texto and eur(p.precio_total_cliente) in texto
    assert "IVA no incluido" not in texto


def test_pdf_profesional_sin_iva_lleva_la_nota_de_iva_no_incluido(db, tmp_path, monkeypatch):
    monkeypatch.setattr(generador_presupuesto, "OUTPUT_DIR", str(tmp_path))
    p = router.crear_presupuesto(peticion(db, iva_pct=D("0")), db)

    texto = texto_pdf(router.descargar_pdf_presupuesto(p.id, "cliente", "profesional", db).path)

    assert "IVA no incluido" in texto and "Base imponible" not in texto


@pytest.mark.parametrize("iva", ["21", "0"])
def test_pdf_profesional_del_presupuesto_por_items(db, tmp_path, monkeypatch, iva):
    from app.models.presupuesto_items import PresupuestoItems, PresupuestoItemsLinea
    from app.pdf import generador_presupuesto_items as gen

    monkeypatch.setattr(gen, "OUTPUT_DIR", str(tmp_path))
    subtotal = D("200.00")
    pct = D(iva)
    iva_importe = (subtotal * pct / 100).quantize(D("0.01"))
    pi = PresupuestoItems(
        empresa_id=db.query(Empresa).first().id,
        nombre="Cableado oficina",
        cliente_nombre="Cliente SL",
        fecha=date(2026, 10, 7),
        iva_pct=pct,
        subtotal=subtotal,
        iva_importe=iva_importe,
        precio_total_cliente=subtotal + iva_importe,
    )
    pi.lineas.append(
        PresupuestoItemsLinea(
            familia="Cableado", nombre="Punto de red", unidad="ud", cantidad=D("4"), precio_unitario=D("50"), importe=D("200")
        )
    )
    db.add(pi)
    db.commit()

    texto = texto_pdf(gen.generar_pdf_presupuesto_items(pi, "cliente"))

    assert "PRESUPUESTO" in texto and "Punto de red" in texto and "Conforme del cliente" in texto
    assert eur(subtotal) in texto
    assert ("IVA (21 %)" in texto) == (iva == "21")
    assert ("IVA no incluido" in texto) == (iva == "0")
    # el interno sigue siendo el de siempre
    assert "USO INTERNO" in texto_pdf(gen.generar_pdf_presupuesto_items(pi, "interno"))
