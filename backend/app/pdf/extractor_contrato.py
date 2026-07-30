"""
Extracción heurística de datos de un contrato de trabajo en PDF ya firmado,
para pre-rellenar el formulario de alta de contrato y que el usuario solo
tenga que revisar y confirmar (no se guarda nada automáticamente).

Esto NO es un parser fiable al 100%: los contratos varían mucho de formato.
Se buscan patrones de texto habituales en contratos españoles y se devuelve
`None` en los campos que no se han podido reconocer con confianza, para que
el usuario los rellene a mano.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO

from pypdf import PdfReader

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

TIPOS_CONTRATO_PATRONES = [
    (r"contrato\s+(?:de\s+trabajo\s+)?indefinido", "indefinido"),
    (r"contrato\s+(?:de\s+trabajo\s+)?para\s+la\s+formaci[oó]n", "formacion"),
    (r"contrato\s+(?:de\s+trabajo\s+)?en\s+pr[aá]cticas", "practicas"),
    (r"contrato\s+(?:de\s+trabajo\s+)?temporal", "temporal"),
    (r"contrato\s+(?:de\s+trabajo\s+)?de\s+duraci[oó]n\s+determinada", "temporal"),
]


def extraer_texto_pdf(contenido_pdf: bytes) -> str:
    lector = PdfReader(BytesIO(contenido_pdf))
    partes = []
    for pagina in lector.pages:
        texto = pagina.extract_text() or ""
        partes.append(texto)
    return "\n".join(partes)


def _buscar_fecha(texto: str) -> date | None:
    # dd/mm/yyyy o dd-mm-yyyy
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", texto)
    if m:
        dia, mes, anio = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(anio, mes, dia)
        except ValueError:
            pass

    # "1 de enero de 2026"
    m = re.search(
        r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b", texto, re.IGNORECASE
    )
    if m:
        dia = int(m.group(1))
        mes = MESES.get(m.group(2).lower())
        anio = int(m.group(3))
        if mes:
            try:
                return date(anio, mes, dia)
            except ValueError:
                pass

    return None


def _buscar_fecha_inicio(texto: str) -> date | None:
    patrones_contexto = [
        r"fecha\s+de\s+inicio[^\n]{0,40}",
        r"iniciar[aá]\s+su\s+relaci[oó]n\s+laboral[^\n]{0,40}",
        r"con\s+efectos?\s+(?:del?|de\s+día)[^\n]{0,40}",
        r"a\s+partir\s+del?\s+d[ií]a[^\n]{0,40}",
        r"comienza\s+a\s+prestar\s+servicios[^\n]{0,40}",
    ]
    for patron in patrones_contexto:
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            fecha = _buscar_fecha(m.group(0))
            if fecha:
                return fecha
    # Fallback: primera fecha que aparezca en todo el documento
    return _buscar_fecha(texto)


def _buscar_tipo_contrato(texto: str) -> str | None:
    for patron, tipo in TIPOS_CONTRATO_PATRONES:
        if re.search(patron, texto, re.IGNORECASE):
            return tipo
    return None


def _buscar_jornada_pct(texto: str) -> Decimal | None:
    if re.search(r"jornada\s+completa", texto, re.IGNORECASE):
        return Decimal("100")
    if re.search(r"media\s+jornada", texto, re.IGNORECASE):
        return Decimal("50")
    m = re.search(
        r"jornada\s+parcial[^\n]{0,40}?(\d{1,3}(?:[.,]\d+)?)\s*%", texto, re.IGNORECASE
    )
    if m:
        try:
            return Decimal(m.group(1).replace(",", "."))
        except InvalidOperation:
            return None
    return None


def _buscar_salario_mensual(texto: str) -> Decimal | None:
    patrones = [
        r"salario\s+(?:mensual\s+)?bruto[^\n]{0,40}?(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*(?:€|eur\.?|euros)",
        r"retribuci[oó]n\s+mensual[^\n]{0,40}?(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*(?:€|eur\.?|euros)",
        r"salario\s+mensual[^\n]{0,40}?(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*(?:€|eur\.?|euros)",
    ]
    for patron in patrones:
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            crudo = m.group(1).replace(" ", "").replace(".", "").replace(",", ".")
            try:
                return Decimal(crudo)
            except InvalidOperation:
                continue
    return None


def _buscar_texto_tras_etiqueta(texto: str, etiquetas: list[str]) -> str | None:
    for etiqueta in etiquetas:
        m = re.search(rf"{etiqueta}\s*:?\s*([^\n]{{2,60}})", texto, re.IGNORECASE)
        if m:
            valor = m.group(1).strip(" .:-")
            if valor:
                return valor
    return None


def extraer_datos_contrato(contenido_pdf: bytes) -> dict:
    texto = extraer_texto_pdf(contenido_pdf)

    fecha_inicio = _buscar_fecha_inicio(texto)
    tipo_contrato = _buscar_tipo_contrato(texto)
    jornada_porcentaje = _buscar_jornada_pct(texto)
    salario_pactado_mensual = _buscar_salario_mensual(texto)
    puesto_trabajo = _buscar_texto_tras_etiqueta(
        texto, ["puesto de trabajo", "categor[ií]a profesional", "puesto"]
    )

    return {
        "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
        "tipo_contrato": tipo_contrato,
        "jornada_porcentaje": str(jornada_porcentaje) if jornada_porcentaje is not None else None,
        "salario_pactado_mensual": str(salario_pactado_mensual) if salario_pactado_mensual is not None else None,
        "puesto_trabajo": puesto_trabajo,
        "texto_extraido_preview": texto[:1500],
    }
