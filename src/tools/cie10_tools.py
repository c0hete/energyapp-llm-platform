"""
Herramientas CIE-10 para Tool Calling

Permite a Qwen buscar códigos médicos en la base de datos real.
"""
import httpx
from typing import Dict, Any


async def search_cie10_tool(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Busca códigos CIE-10 en la base de datos por término médico.

    Args:
        query: Término de búsqueda (enfermedad, síntoma, diagnóstico)
        limit: Número máximo de resultados (1-50)

    Returns:
        Lista de códigos CIE-10 encontrados
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8001/cie10/search",
            params={"q": query, "limit": min(limit, 50)},
            timeout=10.0
        )
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json(),
            "query": query
        }


async def get_cie10_code_tool(code: str) -> Dict[str, Any]:
    """
    Obtiene información detallada de un código CIE-10 específico.

    Args:
        code: Código CIE-10 exacto (ej: E10, I10, A00)

    Returns:
        Información del código CIE-10
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8001/cie10/{code}",
            timeout=10.0
        )
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json(),
            "code": code
        }


async def execute_cie10_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ejecuta una herramienta CIE-10 basada en el nombre y argumentos.

    Args:
        tool_name: Nombre de la herramienta a ejecutar
        arguments: Argumentos de la herramienta

    Returns:
        Resultado de la ejecución
    """
    try:
        if tool_name == "search_cie10":
            return await search_cie10_tool(
                query=arguments.get("query", ""),
                limit=arguments.get("limit", 10)
            )
        elif tool_name == "get_cie10_code":
            return await get_cie10_code_tool(
                code=arguments.get("code", "")
            )
        else:
            return {
                "success": False,
                "error": f"Tool desconocida: {tool_name}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
