#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/energyapp-llm-platform')

from src.db import SessionLocal
from src.models import User

session = SessionLocal()

print("\n" + "="*80)
print("ESTADO 2FA DE TODOS LOS USUARIOS")
print("="*80 + "\n")

users = session.query(User).order_by(User.id).all()

print("%-5s | %-35s | %-15s | 2FA Enabled | 2FA Configured" % ("ID", "Email", "Role"))
print("-"*80)

for user in users:
    enabled = "✓ YES" if user.totp_enabled else "✗ NO "
    configured = "✓ YES" if user.totp_secret else "✗ NO "
    print("%-5d | %-35s | %-15s | %-11s | %s" % (user.id, user.email, user.role, enabled, configured))

print("\n" + "="*80)
print("INFORMACIÓN IMPORTANTE")
print("="*80)

admin_user = session.query(User).filter(User.email == "administrador@alvaradomazzei.cl").first()

if admin_user:
    print("\nUsuario: administrador@alvaradomazzei.cl")
    print("  - ID: %d" % admin_user.id)
    print("  - Role: %s" % admin_user.role)
    print("  - Active: %s" % ("YES" if admin_user.active else "NO"))
    print("  - TOTP Enabled: %s" % ("YES" if admin_user.totp_enabled else "NO"))
    print("  - TOTP Secret Configured: %s" % ("YES" if admin_user.totp_secret else "NO"))

    if admin_user.totp_enabled:
        print("\n⚠️  2FA ESTÁ HABILITADO para este usuario")
        print("   El usuario necesita un código TOTP para loguear")
    else:
        print("\n✓ 2FA está deshabilitado para este usuario")
else:
    print("\n✗ No se encontró el usuario administrador@alvaradomazzei.cl")

print("\n" + "="*80 + "\n")

session.close()
