import secrets

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./payroll.db"
    # Lista separada por comas, ej: "http://localhost:3000,https://mi-app.vercel.app"
    cors_origins_raw: str = Field(default="http://localhost:3000", validation_alias="CORS_ORIGINS")

    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720  # 12 horas

    admin_default_email: str = "admin@example.com"
    admin_default_nombre: str = "Administrador"
    admin_default_password: str = "cambiar-esta-clave"

    # URL pública del frontend, usada para construir el enlace del correo de
    # recuperación de contraseña (ej. https://frontend-fcc-ontrol.vercel.app)
    frontend_url: str = "http://localhost:3000"

    # Envío de correo de recuperación de contraseña vía la API HTTP de Resend
    # (https://resend.com). Se usa una API sobre HTTPS y no SMTP porque varios
    # proveedores de hosting (Render incluido, en su plan gratuito) bloquean
    # las conexiones salientes por los puertos SMTP (25/465/587).
    # Si resend_api_key está vacío, no se envía el correo real: el enlace se
    # registra en el log del servidor (útil en desarrollo local).
    resend_api_key: str = ""
    resend_from: str = "PAYROLL CREATOR <onboarding@resend.dev>"
    reset_password_token_minutos: int = 30

    class Config:
        env_file = ".env"
        populate_by_name = True

    @property
    def cors_origins(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins_raw.split(",") if origen.strip()]


settings = Settings()
