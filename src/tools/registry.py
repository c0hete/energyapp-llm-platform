"""
Registro centralizado de herramientas disponibles para Qwen
"""

# Definiciones de tools en formato estándar OpenAI/Qwen
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_cie10",
            "description": "Busca códigos CIE-10 (Clasificación Internacional de Enfermedades) por término médico en español. Retorna una lista de códigos relevantes con sus descripciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda médico (enfermedad, síntoma, diagnóstico). Ejemplo: 'diabetes', 'hipertensión', 'migraña'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de resultados a retornar",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cie10_code",
            "description": "Obtiene información detallada de un código CIE-10 específico. Útil cuando el usuario proporciona un código exacto o cuando ya sabes el código a consultar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Código CIE-10 exacto. Ejemplos: 'E10', 'I10', 'A00', 'J11'"
                    }
                },
                "required": ["code"]
            }
        }
    }
]


def get_tool_definitions() -> list:
    """Retorna las definiciones de todas las herramientas disponibles"""
    return AVAILABLE_TOOLS
