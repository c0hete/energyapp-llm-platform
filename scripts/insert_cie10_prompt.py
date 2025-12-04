"""
Script para insertar el system prompt de CIE-10 en la base de datos
Uso: python scripts/insert_cie10_prompt.py
"""
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import SessionLocal
from src.models import SystemPrompt

PROMPT_CONTENT = """Eres un asistente médico especializado. Tienes acceso a una base de datos completa de códigos CIE-10 (Clasificación Internacional de Enfermedades).

IMPORTANTE: Cuando el usuario pregunte por códigos médicos, diagnósticos o enfermedades, DEBES buscar en la base de datos CIE-10 antes de responder.

Para buscar códigos CIE-10:
1. Usa el endpoint interno: GET http://localhost:8001/cie10/search?q=<término>&limit=<número>
2. También puedes obtener un código específico: GET http://localhost:8001/cie10/<código>

Ejemplos de uso:
- Usuario pregunta por "diabetes" → Buscar: http://localhost:8001/cie10/search?q=diabetes&limit=5
- Usuario pregunta por "hipertensión arterial" → Buscar: http://localhost:8001/cie10/search?q=hipertension
- Usuario menciona código "E10" → Verificar: http://localhost:8001/cie10/E10

FORMATO DE RESPUESTA:
Cuando encuentres códigos CIE-10 relevantes, presenta la información así:

📋 **Código CIE-10**: E10
📝 **Descripción**: Diabetes mellitus insulinodependiente
🏷️ **Categoría**: E10-E14 (Diabetes mellitus)

Códigos relacionados:
- E10.0: Con coma
- E10.1: Con cetoacidosis
- E10.2: Con complicaciones renales

REGLAS:
- Siempre verifica la ortografía del término médico antes de buscar
- Si no encuentras resultados, sugiere términos alternativos
- Explica brevemente la condición médica además de dar el código
- Menciona si el código es un rango (categoría) o código específico"""


def insert_cie10_prompt():
    """Inserta el system prompt de CIE-10 en la base de datos"""
    db = SessionLocal()

    try:
        # Verificar si ya existe
        existing = db.query(SystemPrompt).filter(
            SystemPrompt.name == "Asistente Médico CIE-10"
        ).first()

        if existing:
            print("❌ El prompt 'Asistente Médico CIE-10' ya existe en la base de datos")
            print(f"   ID: {existing.id}")
            print(f"   Activo: {existing.is_active}")
            print(f"   Por defecto: {existing.is_default}")
            return

        # Crear nuevo prompt
        prompt = SystemPrompt(
            name="Asistente Médico CIE-10",
            description="Prompt para asistencia médica con acceso a códigos CIE-10",
            content=PROMPT_CONTENT,
            is_default=False,
            is_active=True,
            created_by=1  # ID del admin
        )

        db.add(prompt)
        db.commit()
        db.refresh(prompt)

        print("✅ System prompt de CIE-10 insertado correctamente")
        print(f"   ID: {prompt.id}")
        print(f"   Nombre: {prompt.name}")
        print(f"   Activo: {prompt.is_active}")
        print("")
        print("📋 Próximos pasos:")
        print("   1. En el frontend, el usuario puede seleccionar este prompt del dropdown")
        print("   2. Al chatear, Qwen tendrá acceso a los 14,498 códigos CIE-10")
        print("   3. Ejemplo de pregunta: '¿Qué código CIE-10 es diabetes tipo 1?'")

    except Exception as e:
        print(f"❌ Error al insertar el prompt: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("INSERTAR SYSTEM PROMPT DE CIE-10")
    print("=" * 60)
    print("")

    insert_cie10_prompt()

    print("")
    print("=" * 60)
    print("COMPLETADO")
    print("=" * 60)
