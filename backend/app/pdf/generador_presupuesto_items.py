import os

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from app.models.presupuesto_items import PresupuestoItems
from app.version import FULL_VERSION

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_pdfs")

_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _fecha_es(fecha) -> str:
    if fecha is None:
        return "-"
    return fecha.strftime("%d-%m-%Y")


def generar_pdf_presupuesto_items(presupuesto: PresupuestoItems, tipo: str = "cliente") -> str:
    """
    tipo="cliente": por línea solo se ve partida, unidad, cantidad, precio
    unitario e importe (el margen ya viene incluido en el precio, no se
    desglosa coste/margen).
    tipo="interno": añade coste directo unitario y margen % de cada línea,
    para control interno.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    hay_descuentos = any(l.descuento_pct for l in presupuesto.lineas)
    # Familia, Partida, Unidad, Cantidad, Precio unit. = 5 columnas base;
    # +2 si es interno (coste unitario, margen %); +1 si hay descuentos.
    columnas_antes_importe = 5 + (2 if tipo == "interno" else 0) + (1 if hay_descuentos else 0)

    template = _env.get_template("presupuesto_items.html")
    html_str = template.render(
        presupuesto=presupuesto,
        empresa=presupuesto.empresa,
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
