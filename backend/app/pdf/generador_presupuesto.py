import os
from decimal import Decimal

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from app.models.presupuesto import Presupuesto
from app.version import FULL_VERSION

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_pdfs")

_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _fecha_es(fecha) -> str:
    if fecha is None:
        return "-"
    return fecha.strftime("%d-%m-%Y")


def generar_pdf_presupuesto(presupuesto: Presupuesto, tipo: str = "cliente") -> str:
    """
    tipo="cliente": partidas con el precio de venta ya incluido (margen y
    gastos generales repartidos proporcionalmente), sin revelar el coste
    real ni el margen — lo que se envía normalmente a un cliente.
    tipo="interno": desglose completo (coste directo, gastos generales,
    margen, IVA) para uso propio de la empresa.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Factor único para repartir gastos generales + margen proporcionalmente
    # sobre cada partida en la versión "cliente", sin revelar el coste real
    # ni el margen de cada una — el cliente solo ve el precio de venta.
    coste_directo_total = Decimal(presupuesto.coste_directo_total)
    factor_venta = (
        (Decimal(presupuesto.precio_venta) / coste_directo_total) if coste_directo_total > 0 else Decimal("1")
    )

    lineas_personal_vista = []
    for linea in presupuesto.lineas_personal:
        coste_mano_obra = Decimal(linea.coste_mano_obra_total)
        coste_dietas = Decimal(linea.coste_dietas_total)
        lineas_personal_vista.append(
            {
                "categoria_nombre": linea.categoria.nombre,
                "categoria_grupo": linea.categoria.grupo,
                "cantidad_personas": linea.cantidad_personas,
                "dias_dedicacion": linea.dias_dedicacion,
                "jornada_porcentaje": linea.jornada_porcentaje,
                "numero_medias_dietas": linea.numero_medias_dietas,
                "numero_dietas_completas_cortas": linea.numero_dietas_completas_cortas,
                "numero_dietas_completas_largas": linea.numero_dietas_completas_largas,
                "coste_mano_obra_total": coste_mano_obra,
                "coste_dietas_total": coste_dietas,
                "precio_venta_mano_obra": (coste_mano_obra * factor_venta).quantize(Decimal("0.01")),
                "precio_venta_dietas": (coste_dietas * factor_venta).quantize(Decimal("0.01")),
            }
        )

    lineas_otros_vista = []
    for otro in presupuesto.lineas_otros:
        importe_coste = Decimal(otro.importe)
        lineas_otros_vista.append(
            {
                "concepto": otro.concepto,
                "cantidad": otro.cantidad,
                "precio_unitario": otro.precio_unitario,
                "importe": importe_coste,
                "precio_venta_linea": (importe_coste * factor_venta).quantize(Decimal("0.01")),
            }
        )

    # Totales de las 3 categorías a precio de venta (para la versión cliente).
    precio_venta_mano_obra = (Decimal(presupuesto.coste_directo_mano_obra) * factor_venta).quantize(Decimal("0.01"))
    precio_venta_dietas = (Decimal(presupuesto.coste_directo_dietas) * factor_venta).quantize(Decimal("0.01"))
    precio_venta_materiales = (Decimal(presupuesto.coste_directo_otros) * factor_venta).quantize(Decimal("0.01"))

    template = _env.get_template("presupuesto.html")
    html_str = template.render(
        presupuesto=presupuesto,
        empresa=presupuesto.empresa,
        convenio=presupuesto.convenio,
        tipo=tipo,
        fecha=_fecha_es(presupuesto.fecha),
        lineas_personal=lineas_personal_vista,
        lineas_otros=lineas_otros_vista,
        precio_venta_mano_obra=precio_venta_mano_obra,
        precio_venta_dietas=precio_venta_dietas,
        precio_venta_materiales=precio_venta_materiales,
        app_version=FULL_VERSION,
    )

    nombre_archivo = f"presupuesto_{presupuesto.id}_{tipo}.pdf"
    ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)
    with open(ruta_salida, "wb") as archivo_salida:
        resultado = pisa.CreatePDF(html_str, dest=archivo_salida)
    if resultado.err:
        raise RuntimeError(f"Error generando el PDF del presupuesto {presupuesto.id}")

    return ruta_salida
