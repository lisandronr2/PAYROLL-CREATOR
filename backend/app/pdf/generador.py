import os

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from app.models.nomina import Nomina
from app.version import FULL_VERSION

MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_pdfs")

_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def generar_pdf_nomina(nomina: Nomina) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    contrato = nomina.contrato
    trabajador = contrato.trabajador
    empresa = trabajador.empresa
    categoria = contrato.categoria

    lineas_devengo = [l for l in nomina.lineas if l.bloque == "devengo"]
    lineas_deduccion = [
        l for l in nomina.lineas if l.bloque in ("deduccion", "cotizacion_trabajador")
    ]
    lineas_empresa = [l for l in nomina.lineas if l.bloque == "cotizacion_empresa"]

    template = _env.get_template("nomina.html")
    html_str = template.render(
        nomina=nomina,
        empresa=empresa,
        trabajador=trabajador,
        categoria_nombre=categoria.nombre,
        grupo_cotizacion=categoria.grupo_cotizacion,
        convenio_nombre=contrato.convenio.nombre,
        mes_nombre=MESES_ES[nomina.periodo_mes],
        lineas_devengo=lineas_devengo,
        lineas_deduccion=lineas_deduccion,
        lineas_empresa=lineas_empresa,
        app_version=FULL_VERSION,
    )

    nombre_archivo = f"nomina_{nomina.id}.pdf"
    ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)
    with open(ruta_salida, "wb") as archivo_salida:
        resultado = pisa.CreatePDF(html_str, dest=archivo_salida)
    if resultado.err:
        raise RuntimeError(f"Error generando el PDF de la nómina {nomina.id}")

    nomina.pdf_path = ruta_salida
    return ruta_salida
