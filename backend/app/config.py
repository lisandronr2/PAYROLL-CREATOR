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

    class Config:
        env_file = ".env"
        populate_by_name = True

    @property
    def cors_origins(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins_raw.split(",") if origen.strip()]


settings = Settings()
