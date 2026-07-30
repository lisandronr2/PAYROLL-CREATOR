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

    # SMTP para el correo de recuperación de contraseña. Si smtp_user o
    # smtp_password están vacíos, no se envía el correo real: el enlace se
    # registra en el log del servidor (útil en desarrollo local).
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    reset_password_token_minutos: int = 30

    class Config:
        env_file = ".env"
        populate_by_name = True

    @property
    def cors_origins(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins_raw.split(",") if origen.strip()]


settings = Settings()
