import os
from datetime import timedelta
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from app.models.presupuesto_items import PresupuestoItems
from app.numeracion import numero_visible
from app.pdf.logos import logo_de_empresa
from app.pdf.presupuesto_cliente import DIAS_VALIDEZ, cant, eur, totales_de
from app.version import FULL_VERSION

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_pdfs")

_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
_env.filters["eur"] = eur
_env.filters["cant"] = cant

FORMATOS = ("clasico", "profesional")


def _fecha_es(fecha) -> str:
    if fecha is None:
        return "-"
    return fecha.strftime("%d-%m-%Y")


def generar_pdf_presupuesto_items(presupuesto: PresupuestoItems, tipo: str = "cliente", formato: str = "profesional") -> str:
    """
    tipo="cliente": por línea solo se ve partida, unidad, cantidad, precio
    unitario e importe (el margen ya viene incluido en el precio, no se
    desglosa coste/margen).
    tipo="interno": añade coste directo unitario y margen % de cada línea,
    para control interno.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if tipo == "cliente" and formato == "profesional":
        return _generar_pdf_cliente_profesional(presupuesto)

    hay_descuentos = any(l.descuento_pct for l in presupuesto.lineas)
    # Familia, Partida, Unidad, Cantidad, Precio unit. = 5 columnas base;
    # +2 si es interno (coste unitario, margen %); +1 si hay descuentos.
    columnas_antes_importe = 5 + (2 if tipo == "interno" else 0) + (1 if hay_descuentos else 0)

    template = _env.get_template("presupuesto_items.html")
    html_str = template.render(
        presupuesto=presupuesto,
        empresa=presupuesto.empresa,
        logo=logo_de_empresa(presupuesto.empresa),
        tipo=tipo,
        fecha=_fecha_es(presupuesto.fecha),
        lineas=presupuesto.lineas,
        hay_descuentos=hay_descuentos,
        columnas_antes_importe=columnas_antes_importe,
        app_version=FULL_VERSION,
    )

    nombre_archivo = f"presupuesto_items_{presupuesto.id}_{tipo}.pdf"
    ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)
    with open(ruta_salida, "wb") as archivo_salida:
        resultado = pisa.CreatePDF(html_str, dest=archivo_salida)
    if resultado.err:
        raise RuntimeError(f"Error generando el PDF del presupuesto por items {presupuesto.id}")

    return ruta_salida


def _generar_pdf_cliente_profesional(presupuesto: PresupuestoItems) -> str:
    fecha = presupuesto.fecha
    datos = SimpleNamespace(
        numero=numero_visible(presupuesto, "I"),
        fecha=fecha.strftime("%d/%m/%Y"),
        valido_hasta=(fecha + timedelta(days=DIAS_VALIDEZ)).strftime("%d/%m/%Y"),
        dias_validez=DIAS_VALIDEZ,
    )
    template = _env.get_template("presupuesto_items_cliente_profesional.html")
    html_str = template.render(
        presupuesto=presupuesto,
        empresa=presupuesto.empresa,
        datos=datos,
        t=totales_de(presupuesto, presupuesto.subtotal),
        logo=logo_de_empresa(presupuesto.empresa),
        lineas=presupuesto.lineas,
        hay_descuentos=any(l.descuento_pct for l in presupuesto.lineas),
    )
    ruta_salida = os.path.join(OUTPUT_DIR, f"presupuesto_items_{presupuesto.id}_cliente_profesional.pdf")
    with open(ruta_salida, "wb") as archivo_salida:
        resultado = pisa.CreatePDF(html_str, dest=archivo_salida)
    if resultado.err:
        raise RuntimeError(f"Error generando el PDF profesional del presupuesto por items {presupuesto.id}")
    return ruta_salida
