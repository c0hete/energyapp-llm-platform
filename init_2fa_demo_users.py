#!/usr/bin/env python3
"""
Script para inicializar cuentas de demostración con 2FA (TOTP) habilitado.

Crea/actualiza tres usuarios demo con TOTP pre-configurado.
Los secrets se guardan en la consola para que el administrador los configure en
sus apps autenticadoras (Google Authenticator, Authy, etc).

Uso:
    python init_2fa_demo_users.py
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.db import SessionLocal, engine
from src.models import Base, User
from src.auth import hash_password
from src.totp import setup_2fa

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Cuentas demo con 2FA
DEMO_USERS = [
    {"email": "administrador@alvaradomazzei.cl", "password": "admin123", "role": "admin"},
    {"email": "trabajador@alvaradomazzei.cl", "password": "worker123", "role": "trabajador"},
    {"email": "supervisor@alvaradomazzei.cl", "password": "supervisor123", "role": "supervisor"},
]

db = SessionLocal()

print("\n" + "="*60)
print("INICIALIZANDO CUENTAS DEMO CON 2FA (TOTP)")
print("="*60 + "\n")

for user_data in DEMO_USERS:
    email = user_data["email"]
    password = user_data["password"]
    role = user_data["role"]

    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.email == email).first()  # type: ignore

    if existing_user:
        print(f"[UPDATE] Usuario '{email}' ya existe, actualizando 2FA...")
        user = existing_user
    else:
        print(f"[CREATE] Creando usuario '{email}' (rol: {role})...")
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            active=True,
        )
        db.add(user)
        db.flush()  # Asegurar que se asigne el ID

    # Generar secret TOTP y habilitar 2FA
    secret, qr_code = setup_2fa(email)
    user.totp_secret = secret  # type: ignore
    user.totp_enabled = True  # type: ignore

    db.commit()

    print(f"\n   Email: {email}")
    print(f"   Password: {password}")
    print(f"   Role: {role}")
    print(f"   2FA Habilitado: ✓")
    print(f"   TOTP Secret: {secret}")
    print(f"\n   ⚠️  GUARDA ESTE SECRET EN UN LUGAR SEGURO")
    print(f"   Usa este secret en tu app autenticadora (Google Authenticator, Authy, etc)")
    print(f"   Forma alternativa: Escanea este QR:")
    print(f"   [QR CODE - ver en navegador o usar provisioning_uri]\n")

print("="*60)
print("✅ Inicialización completada")
print("="*60)
print("\nProximos pasos:")
print("1. Guarda los secrets TOTP en un lugar seguro")
print("2. Abre https://alvaradomazzei.cl/energyapp en tu navegador")
print("3. Intenta hacer login - verás la pantalla de 2FA")
print("4. Abre tu app autenticadora y copia el código")
print("5. Pégalo en la pantalla de 2FA\n")

db.close()
