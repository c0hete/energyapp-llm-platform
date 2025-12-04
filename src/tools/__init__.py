"""
Sistema de Tools (Function Calling) para Qwen

Este módulo implementa el sistema de herramientas que permite a Qwen
ejecutar funciones reales en el backend, como búsquedas en CIE-10.
"""

from .cie10_tools import search_cie10_tool, get_cie10_code_tool, execute_cie10_tool
from .registry import AVAILABLE_TOOLS, get_tool_definitions

__all__ = [
    "search_cie10_tool",
    "get_cie10_code_tool",
    "execute_cie10_tool",
    "AVAILABLE_TOOLS",
    "get_tool_definitions",
]
