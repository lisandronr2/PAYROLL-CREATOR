import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_usuario, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.email_utils import enviar_email_recuperacion
from app.models.usuario import Usuario
from app.schemas.usuario import (
    LoginRequest,
    RestablecerPasswordRequest,
    SolicitarRecuperacionRequest,
    TokenOut,
    UsuarioOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

MENSAJE_RECUPERACION_GENERICO = (
    "Si el correo existe en el sistema, se ha enviado un enlace de recuperación."
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _enmascarar_email(email: str) -> str:
    if not email or "@" not in email:
        return "(vacío)"
    local, dominio = email.split("@", 1)
    return f"{local[:2]}***@{dominio}"


# Endpoint temporal de diagnóstico SMTP, protegido por un token fijo en código
# (no expone contraseñas, solo confirma qué configuración está realmente
# cargada en el proceso en ejecución, y si el login SMTP funciona). Quitar
# una vez resuelto el problema de entrega de correos.
DIAG_TOKEN = "payroll-diag-2026-smtp"


@router.get("/diagnostico-smtp")
def diagnostico_smtp(token: str):
    if token != DIAG_TOKEN:
        raise HTTPException(status_code=404)

    resultado = {
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_use_tls": settings.smtp_use_tls,
        "smtp_user": _enmascarar_email(settings.smtp_user),
        "smtp_from": _enmascarar_email(settings.smtp_from),
        "frontend_url": settings.frontend_url,
        "smtp_configurado": bool(settings.smtp_user and settings.smtp_password),
        "smtp_password_longitud": len(settings.smtp_password or ""),
    }

    if resultado["smtp_configurado"]:
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as servidor:
                if settings.smtp_use_tls:
                    servidor.starttls()
                servidor.login(settings.smtp_user, settings.smtp_password)
            resultado["login_smtp"] = "OK"
        except Exception as exc:
            resultado["login_smtp"] = f"FALLÓ: {type(exc).__name__}: {exc}"

    return resultado


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario or not usuario.activo or not verify_password(payload.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = create_access_token(usuario)
    return TokenOut(access_token=token, usuario=usuario)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_usuario)):
    return usuario


@router.post("/solicitar-recuperacion")
def solicitar_recuperacion(payload: SolicitarRecuperacionRequest, db: Session = Depends(get_db)):
    """
    No revela si el correo existe o no (evita enumeración de usuarios): la
    respuesta es siempre el mismo mensaje genérico, se envíe o no el correo.
    """
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if usuario and usuario.activo:
        token = secrets.token_urlsafe(32)
        usuario.reset_token_hash = _hash_token(token)
        # Se guarda como UTC "naive" (sin tzinfo) porque SQLite no conserva la
        # zona horaria al leer de vuelta la columna, lo que rompería la
        # comparación con datetime "aware" al validar el token.
        usuario.reset_token_expira = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            minutes=settings.reset_password_token_minutos
        )
        db.commit()

        enlace = f"{settings.frontend_url}/restablecer-password?token={token}"
        enviar_email_recuperacion(usuario.email, usuario.nombre, enlace)

    return {"detail": MENSAJE_RECUPERACION_GENERICO}


@router.post("/restablecer-password")
def restablecer_password(payload: RestablecerPasswordRequest, db: Session = Depends(get_db)):
    token_hash = _hash_token(payload.token)
    usuario = db.query(Usuario).filter(Usuario.reset_token_hash == token_hash).first()

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    if (
        not usuario
        or not usuario.reset_token_expira
        or usuario.reset_token_expira < ahora
    ):
        raise HTTPException(status_code=400, detail="El enlace de recuperación no es válido o ha caducado")

    usuario.password_hash = hash_password(payload.password)
    usuario.activo = True  # la nueva contraseña se activa de inmediato
    usuario.reset_token_hash = None
    usuario.reset_token_expira = None
    db.commit()

    return {"detail": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}
