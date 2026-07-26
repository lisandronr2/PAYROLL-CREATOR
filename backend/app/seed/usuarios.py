from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import settings
from app.models.usuario import Usuario


def seed_usuario_admin(db: Session) -> None:
    if db.query(Usuario).first() is not None:
        return

    admin = Usuario(
        email=settings.admin_default_email,
        nombre=settings.admin_default_nombre,
        password_hash=hash_password(settings.admin_default_password),
        rol="admin",
        activo=True,
    )
    db.add(admin)
    db.commit()
    print(
        f"Usuario admin creado: {settings.admin_default_email} "
        f"(cambia la contraseña por defecto en cuanto puedas)."
    )
