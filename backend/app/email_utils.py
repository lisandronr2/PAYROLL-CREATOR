"""
Envío de correos transaccionales (por ahora, solo recuperación de contraseña)
vía la API HTTP de Resend (https://resend.com/docs/api-reference/emails/send-email).

Se usa una API sobre HTTPS (puerto 443) en vez de SMTP porque varios
proveedores de hosting — Render incluido, en su plan gratuito — bloquean las
conexiones salientes por los puertos SMTP (25/465/587), lo que hace que un
envío por smtplib nunca llegue a conectar (ver commit que añadió este
comentario para el diagnóstico completo).

Si RESEND_API_KEY no está configurado, no se envía el correo real: el enlace
se registra en el log del servidor para poder seguir probando el flujo
manualmente en desarrollo local.
"""
import json
import logging
import urllib.error
import urllib.request

from app.config import settings

logger = logging.getLogger("payroll_creator.email")

RESEND_API_URL = "https://api.resend.com/emails"


def _resend_configurado() -> bool:
    return bool(settings.resend_api_key)


def enviar_email_recuperacion(destinatario: str, nombre: str, enlace: str) -> None:
    asunto = "Recuperación de contraseña — PAYROLL CREATOR"
    cuerpo_texto = (
        f"Hola {nombre},\n\n"
        "Hemos recibido una solicitud para restablecer tu contraseña en PAYROLL CREATOR.\n"
        f"Para elegir una nueva contraseña, entra en este enlace (caduca en "
        f"{settings.reset_password_token_minutos} minutos):\n\n"
        f"{enlace}\n\n"
        "Si no has solicitado este cambio, puedes ignorar este correo: tu contraseña "
        "actual seguirá siendo válida.\n\n"
        "— PAYROLL CREATOR"
    )
    cuerpo_html = (
        f"<p>Hola {nombre},</p>"
        "<p>Hemos recibido una solicitud para restablecer tu contraseña en "
        "<strong>PAYROLL CREATOR</strong>.</p>"
        f"<p>Para elegir una nueva contraseña, entra en este enlace (caduca en "
        f"{settings.reset_password_token_minutos} minutos):</p>"
        f'<p><a href="{enlace}">{enlace}</a></p>'
        "<p>Si no has solicitado este cambio, puedes ignorar este correo: tu contraseña "
        "actual seguirá siendo válida.</p>"
        "<p>— PAYROLL CREATOR</p>"
    )

    if not _resend_configurado():
        logger.warning(
            "Resend no configurado: no se envía correo real. Enlace de recuperación para %s: %s",
            destinatario,
            enlace,
        )
        return

    payload = {
        "from": settings.resend_from,
        "to": [destinatario],
        "subject": asunto,
        "text": cuerpo_texto,
        "html": cuerpo_html,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        RESEND_API_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
            # Cloudflare (delante de la API de Resend) rechaza con "error code:
            # 1010" las peticiones con el User-Agent por defecto de urllib.
            "User-Agent": "PayrollCreator/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as respuesta:
            respuesta.read()
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend respondió {exc.code}: {detalle}") from exc
