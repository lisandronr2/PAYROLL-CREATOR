import os

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from app.models.liquidacion import Liquidacion
from app.pdf.logos import logo_de_empresa
from app.version import FULL_VERSION

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_pdfs")

_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _fecha_es(fecha) -> str:
    return fecha.strftime("%d-%m-%Y") if fecha else "-"


def generar_pdf_liquidacion(liquidacion: Liquidacion, tipo: str = "trabajador") -> str:
    """
    tipo="trabajador": la liquidación para entregar al trabajador (conceptos,
    deducciones, líquido y espacio para firmas); sin el coste de la empresa
    ni las notas internas de cálculo.
    tipo="interno": añade cotiza/tributa de cada concepto, su referencia
    legal, el coste para la empresa y los avisos del cálculo.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    lineas = liquidacion.lineas
    template = _env.get_template("liquidacion.html")
    html_str = template.render(
        liq=liquidacion,
        empresa=liquidacion.contrato.trabajador.empresa,
        logo=logo_de_empresa(liquidacion.contrato.trabajador.empresa),
        tipo=tipo,
        fecha_ingreso=_fecha_es(liquidacion.fecha_ingreso),
        fecha_baja=_fecha_es(liquidacion.fecha_baja),
        fecha_calculo=_fecha_es(liquidacion.creado_en.date()) if liquidacion.creado_en else "-",
        lineas_percibir=[l for l in lineas if l.bloque in ("devengo", "indemnizacion")],
        lineas_deducir=[l for l in lineas if l.bloque in ("descuento", "deduccion")],
        avisos=liquidacion.avisos,
        app_version=FULL_VERSION,
    )

    ruta_salida = os.path.join(OUTPUT_DIR, f"liquidacion_{liquidacion.id}_{tipo}.pdf")
    with open(ruta_salida, "wb") as archivo_salida:
        resultado = pisa.CreatePDF(html_str, dest=archivo_salida)
    if resultado.err:
        raise RuntimeError(f"Error generando el PDF de la liquidación {liquidacion.id}")
    return ruta_salida
