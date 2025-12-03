#!/usr/bin/env python3
"""
Script para migrar roles de 'administrador' a 'admin'
"""
import sys
sys.path.insert(0, '/root/energyapp-llm-platform')

from src.db import SessionLocal
from src.models import User

def migrate_roles():
    session = SessionLocal()

    try:
        print("\n" + "="*70)
        print("MIGRACIÓN DE ROLES: administrador -> admin")
        print("="*70)

        # Verificar usuarios con rol 'administrador'
        admin_users = session.query(User).filter(User.role == "administrador").all()

        if not admin_users:
            print("\n✓ No hay usuarios con rol 'administrador' para migrar")
            print("  Todos los usuarios ya tienen los roles correctos")
            session.close()
            return True

        print("\nEncontrados %d usuario(s) con rol 'administrador':" % len(admin_users))
        for user in admin_users:
            print("  - ID: %d | Email: %s" % (user.id, user.email))

        # Actualizar roles
        print("\nRealizando migración...")
        session.query(User).filter(User.role == "administrador").update({'role': 'admin'})
        session.commit()

        # Verificar que la migración fue exitosa
        migrated_users = session.query(User).filter(User.role == "admin").all()

        print("\n" + "="*70)
        print("✓ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*70)
        print("\nAhora tienes %d usuario(s) con rol 'admin':" % len(migrated_users))
        for user in migrated_users:
            status = "ACTIVE" if user.active else "INACTIVE"
            print("  - ID: %d | Email: %s | %s" % (user.id, user.email, status))

        print("\n✓ Los usuarios 'administrador' ahora son 'admin' en el sistema")
        print("✓ Pueden acceder al panel de administración")

        session.close()
        return True

    except Exception as e:
        print("\n✗ ERROR durante la migración: %s" % str(e))
        session.rollback()
        session.close()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_roles()
    sys.exit(0 if success else 1)
