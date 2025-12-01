from src.db import SessionLocal, Base, engine
from src.models import User
from src.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if not db.query(User).first():
    db.add(User(
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
        active=True
    ))
    db.commit()
    print("Usuario seed admin@example.com / admin123 creado")
else:
    print("Ya existe un usuario, no se crea otro")
db.close()
