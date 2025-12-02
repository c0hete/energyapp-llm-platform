"""Utilidades para TOTP (Time-based One-Time Password) / 2FA"""

import pyotp
import qrcode
from io import BytesIO
import base64
from typing import Tuple


def generate_totp_secret() -> str:
    """Genera un secret base32 aleatorio para TOTP"""
    return pyotp.random_base32()


def get_totp_provisioning_uri(secret: str, email: str, issuer: str = "EnergyApp") -> str:
    """Retorna URI para provisioning (puede convertirse a QR)"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def generate_qr_code_base64(uri: str) -> str:
    """Genera QR code en base64 a partir de URI de provisioning"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convertir a PNG en memoria
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # Codificar a base64
    img_base64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


def verify_totp(secret: str, totp_code: str) -> bool:
    """Verifica si un código TOTP es válido"""
    totp = pyotp.TOTP(secret)
    # Permitir 1 ventana de tiempo en cada dirección (default ±30 segundos)
    return totp.verify(totp_code, valid_window=1)


def setup_2fa(email: str) -> Tuple[str, str]:
    """
    Setup 2FA para un usuario
    Retorna (secret, qr_code_base64)
    """
    secret = generate_totp_secret()
    uri = get_totp_provisioning_uri(secret, email)
    qr_code = generate_qr_code_base64(uri)
    return secret, qr_code
