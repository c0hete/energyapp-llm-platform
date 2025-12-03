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

# Generar datos para HTML
users_data = []

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

    # Guardar datos para HTML
    users_data.append({
        "email": email,
        "password": password,
        "role": role,
        "secret": secret,
        "qr_code": qr_code
    })

# Generar archivo HTML
html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2FA Setup - EnergyApp Demo Users</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0a0e27;
            color: #f5f7fb;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 30px; color: #1f64ff; }
        .users-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .user-card {
            background: #0f172a;
            border: 1px solid #1f2a44;
            border-radius: 8px;
            padding: 20px;
        }
        .user-card h2 {
            color: #1f64ff;
            margin-bottom: 15px;
            font-size: 16px;
            word-break: break-all;
        }
        .info-row {
            margin-bottom: 12px;
            font-size: 14px;
        }
        .label { color: #9fb0d2; font-weight: 500; }
        .value {
            color: #f5f7fb;
            font-family: monospace;
            word-break: break-all;
            margin-top: 4px;
            padding: 8px;
            background: #060b19;
            border-radius: 4px;
            border: 1px solid #1f2a44;
        }
        .secret-copy {
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }
        .secret-copy input {
            flex: 1;
            padding: 8px;
            background: #060b19;
            border: 1px solid #1f2a44;
            color: #f5f7fb;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
        }
        .secret-copy button {
            padding: 8px 16px;
            background: #1f64ff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
        }
        .secret-copy button:hover {
            background: #1b56d9;
        }
        .qr-section {
            text-align: center;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #1f2a44;
        }
        .qr-image {
            max-width: 200px;
            margin: 15px auto;
            background: white;
            padding: 10px;
            border-radius: 8px;
        }
        .qr-image img {
            max-width: 100%;
            display: block;
        }
        .instructions {
            background: #0b1226;
            border-left: 3px solid #1f64ff;
            padding: 15px;
            margin-top: 30px;
            border-radius: 4px;
        }
        .instructions h3 { margin-bottom: 10px; color: #1f64ff; }
        .instructions ol { margin-left: 20px; }
        .instructions li { margin-bottom: 8px; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 2FA Setup - EnergyApp Demo Users</h1>

        <div class="users-grid">
"""

for user in users_data:
    html_content += f"""
        <div class="user-card">
            <h2>{user['email']}</h2>

            <div class="info-row">
                <div class="label">Contraseña:</div>
                <div class="value">{user['password']}</div>
            </div>

            <div class="info-row">
                <div class="label">Rol:</div>
                <div class="value">{user['role'].upper()}</div>
            </div>

            <div class="info-row">
                <div class="label">TOTP Secret:</div>
                <div class="secret-copy">
                    <input type="text" value="{user['secret']}" readonly>
                    <button onclick="copySecret(this)">Copiar</button>
                </div>
            </div>

            <div class="qr-section">
                <div class="label">QR Code:</div>
                <div class="qr-image">
                    <img src="{user['qr_code']}" alt="QR para {user['email']}">
                </div>
                <small style="color: #9fb0d2;">Escanea con Google Authenticator, Authy, Microsoft Authenticator, etc.</small>
            </div>
        </div>
"""

html_content += """
        </div>

        <div class="instructions">
            <h3>📱 Cómo configurar:</h3>
            <ol>
                <li><strong>Instala una app autenticadora:</strong> Google Authenticator, Authy, Microsoft Authenticator, etc.</li>
                <li><strong>Abre la app y toca "+"</strong> para agregar una nueva cuenta</li>
                <li><strong>Opción A - Escanear QR:</strong> Usa la cámara para escanear el código QR de arriba</li>
                <li><strong>Opción B - Ingreso manual:</strong> Selecciona "Ingreso manual" y copia el TOTP Secret</li>
                <li><strong>Ingresa el nombre:</strong> (ej: "administrador@alvaradomazzei.cl")</li>
                <li><strong>Obtén el código:</strong> Tu app generará un código de 6 dígitos cada 30 segundos</li>
                <li><strong>Ingresa el código en login:</strong> Cuando hagas login en EnergyApp, copia el código de tu app</li>
            </ol>
        </div>

        <div class="instructions" style="margin-top: 20px;">
            <h3>⚠️ Importante:</h3>
            <ol>
                <li><strong>Guarda los secrets en un lugar seguro.</strong> Si pierdes acceso a la app autenticadora, necesitarás el secret para recuperar acceso.</li>
                <li><strong>No compartas estos datos.</strong> Cada secret es único y privado.</li>
                <li><strong>Los códigos caducan cada 30 segundos.</strong> Asegúrate que la hora de tu dispositivo esté sincronizada.</li>
            </ol>
        </div>
    </div>

    <script>
        function copySecret(button) {
            const input = button.previousElementSibling;
            input.select();
            document.execCommand('copy');
            const originalText = button.textContent;
            button.textContent = '✓ Copiado';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
        }
    </script>
</body>
</html>
"""

# Guardar HTML
html_file = "/root/energyapp-llm-platform/2fa_setup.html"
with open(html_file, "w") as f:
    f.write(html_content)

print("="*60)
print("✅ Inicialización completada")
print("="*60)
print(f"\n📄 Archivo HTML generado: {html_file}")
print(f"\nPara ver los QR codes y secrets:")
print(f"  1. Abre el archivo: file://{html_file}")
print(f"  2. O descárgalo via SCP: scp root@184.174.33.249:{html_file} .")
print(f"\nProximos pasos:")
print(f"1. Abre el archivo HTML en tu navegador")
print(f"2. Instala Google Authenticator en tu teléfono")
print(f"3. Escanea los QR codes o copia los secrets manualmente")
print(f"4. Intenta hacer login en https://alvaradomazzei.cl/energyapp")
print(f"5. Ingresa email + password")
print(f"6. Copia el código de 6 dígitos de tu app")
print(f"7. Pégalo en la pantalla de 2FA\n")

db.close()
