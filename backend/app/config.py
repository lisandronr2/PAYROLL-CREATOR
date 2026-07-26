import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./payroll.db"
    cors_origins: list[str] = ["http://localhost:3000"]

    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720  # 12 horas

    admin_default_email: str = "admin@example.com"
    admin_default_nombre: str = "Administrador"
    admin_default_password: str = "cambiar-esta-clave"

    class Config:
        env_file = ".env"


settings = Settings()
