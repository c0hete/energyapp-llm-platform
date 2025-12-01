"""Crea un usuario admin seed (admin@example.com / admin123) si no existe."""
import sys
from pathlib import Path

# Asegurar que el root del proyecto este en sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db import SessionLocal, Base, engine  # type: ignore  # noqa: E402
from src.models import User  # type: ignore  # noqa: E402
from src.auth import hash_password  # type: ignore  # noqa: E402


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).first()
        if existing:
            print("Ya existe un usuario, no se crea otro.")
            return
        user = User(
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            role="admin",
            active=True,
        )
        db.add(user)
        db.commit()
        print("Usuario seed admin@example.com / admin123 creado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
