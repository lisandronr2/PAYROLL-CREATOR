"""
Logos de empresa para los PDF (esquina superior izquierda).

Una empresa sin logo asignado muestra solo su nombre en texto. Para añadir
otro logo: guardar el PNG en app/pdf/assets/ y añadir una fila a LOGOS_EMPRESA
con un fragmento del nombre de la empresa (en minúsculas) y el fichero.
"""
import base64
import os
from functools import lru_cache

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# (fragmento del nombre en minúsculas, fichero en assets/)
LOGOS_EMPRESA = [("soluciones mata", "logo_soluciones_mata.png")]

# Proporción alto/ancho de los logos actuales (700 x 862).
PROPORCION_LOGO = 862 / 700


@lru_cache(maxsize=None)
def _como_data_uri(fichero: str) -> str:
    with open(os.path.join(ASSETS_DIR, fichero), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def logo_de_empresa(empresa) -> str | None:
    """Logo de la empresa como data URI (para incrustarlo en el HTML del PDF)."""
    nombre = (empresa.razon_social or "").lower()
    for fragmento, fichero in LOGOS_EMPRESA:
        if fragmento in nombre:
            return _como_data_uri(fichero)
    return None
