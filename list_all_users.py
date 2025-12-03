#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/energyapp-llm-platform')

from src.db import SessionLocal
from src.models import User

session = SessionLocal()
users = session.query(User).order_by(User.id).all()

print("\n" + "="*80)
print("TODOS LOS USUARIOS EN LA BASE DE DATOS")
print("="*80 + "\n")

if not users:
    print("No hay usuarios en la base de datos\n")
else:
    print("%-5s | %-35s | %-15s | %-10s" % ("ID", "Email", "Role", "Status"))
    print("-"*80)
    for user in users:
        status = "ACTIVE" if user.active else "INACTIVE"
        print("%-5d | %-35s | %-15s | %-10s" % (user.id, user.email, user.role, status))

print("\n" + "="*80)
print("RESUMEN")
print("="*80)

role_counts = {}
for user in users:
    role = user.role
    role_counts[role] = role_counts.get(role, 0) + 1

print("\nDistribución de roles:")
for role, count in sorted(role_counts.items()):
    print("  - %s: %d usuario(s)" % (role, count))

print("\nTotal de usuarios: %d" % len(users))
print("="*80 + "\n")

session.close()
