from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    nombre = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(String, nullable=False, default="operador")  # admin | operador
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    # Recuperación de contraseña: se guarda el hash del token (no el token en
    # claro) y su fecha de caducidad, siempre en UTC "naive" (sin tzinfo) para
    # que la comparación sea consistente entre SQLite y Postgres. Ambos
    # campos se limpian al usarse o expirar.
    reset_token_hash = Column(String, nullable=True)
    reset_token_expira = Column(DateTime(timezone=False), nullable=True)
