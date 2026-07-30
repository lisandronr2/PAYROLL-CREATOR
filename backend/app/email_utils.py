"""
Envío de correos transaccionales (por ahora, solo recuperación de contraseña)
vía SMTP. Usa smtplib de la librería estándar para no añadir dependencias.

Si SMTP_USER/SMTP_PASSWORD no están configurados (por ejemplo en desarrollo
local sin .env), no se envía el correo real: el enlace se registra en el log
del servidor para poder seguir probando el flujo manualmente.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("payroll_creator.email")


def _smtp_configurado() -> bool:
    return bool(settings.smtp_user and settings.smtp_password)


def enviar_email_recuperacion(destinatario: str, nombre: str, enlace: str) -> None:
    asunto = "Recuperación de contraseña — PAYROLL CREATOR"
    cuerpo = (
        f"Hola {nombre},\n\n"
        "Hemos recibido una solicitud para restablecer tu contraseña en PAYROLL CREATOR.\n"
        f"Para elegir una nueva contraseña, entra en este enlace (caduca en "
        f"{settings.reset_password_token_minutos} minutos):\n\n"
        f"{enlace}\n\n"
        "Si no has solicitado este cambio, puedes ignorar este correo: tu contraseña "
        "actual seguirá siendo válida.\n\n"
        "— PAYROLL CREATOR"
    )

    if not _smtp_configurado():
        logger.warning(
            "SMTP no configurado: no se envía correo real. Enlace de recuperación para %s: %s",
            destinatario,
            enlace,
        )
        return

    mensaje = MIMEText(cuerpo, "plain", "utf-8")
    mensaje["Subject"] = asunto
    mensaje["From"] = settings.smtp_from or settings.smtp_user
    mensaje["To"] = destinatario

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as servidor:
        if settings.smtp_use_tls:
            servidor.starttls()
        servidor.login(settings.smtp_user, settings.smtp_password)
        servidor.sendmail(mensaje["From"], [destinatario], mensaje.as_string())
