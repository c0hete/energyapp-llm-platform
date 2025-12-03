#!/usr/bin/env python3
"""
Script para deshabilitar 2FA en usuarios específicos
"""
import sys
sys.path.insert(0, '/root/energyapp-llm-platform')

from src.db import SessionLocal
from src.models import User

def disable_2fa():
    session = SessionLocal()

    try:
        print("\n" + "="*80)
        print("DESHABILITAR 2FA PARA USUARIOS")
        print("="*80)

        # Usuarios a actualizar
        target_users = [
            "administrador@alvaradomazzei.cl",
            "trabajador@alvaradomazzei.cl",
            "supervisor@alvaradomazzei.cl"
        ]

        print("\nBuscando usuarios...\n")

        users_to_update = session.query(User).filter(User.email.in_(target_users)).all()

        if not users_to_update:
            print("✗ No se encontraron usuarios para actualizar")
            session.close()
            return False

        print("Encontrados %d usuario(s) con 2FA habilitado:\n" % len(users_to_update))

        for user in users_to_update:
            print("  - %s (Role: %s) | 2FA Enabled: %s" % (user.email, user.role, "✓ YES" if user.totp_enabled else "✗ NO"))

        print("\n" + "-"*80)
        print("Deshabilitando 2FA...\n")

        # Deshabilitar 2FA
        for user in users_to_update:
            user.totp_enabled = False
            # Opcionalmente limpiar el secret (pero lo dejamos por si quieren re-habilitarlo)
            # user.totp_secret = None
            session.add(user)

        session.commit()

        print("✓ 2FA deshabilitado para:")
        for user in users_to_update:
            print("  - %s" % user.email)

        # Verificar cambios
        updated_users = session.query(User).filter(User.email.in_(target_users)).all()

        print("\n" + "="*80)
        print("ESTADO ACTUAL")
        print("="*80 + "\n")

        print("%-35s | %-15s | 2FA Enabled" % ("Email", "Role"))
        print("-"*80)
        for user in updated_users:
            enabled = "✓ YES" if user.totp_enabled else "✗ NO "
            print("%-35s | %-15s | %s" % (user.email, user.role, enabled))

        print("\n" + "="*80)
        print("✓ CAMBIOS APLICADOS EXITOSAMENTE")
        print("="*80)
        print("\nAhora estos usuarios pueden loguear sin código TOTP")
        print("\n" + "="*80 + "\n")

        session.close()
        return True

    except Exception as e:
        print("\n✗ ERROR: %s" % str(e))
        session.rollback()
        session.close()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = disable_2fa()
    sys.exit(0 if success else 1)
