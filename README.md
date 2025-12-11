# EnergyApp LLM Platform

**Chat LLM privado con Tool Calling y Base de Datos CIE-10**

Una plataforma médica de chat basada en LLM ejecutado localmente con privacidad de datos garantizada. Incluye Tool Calling para búsquedas automáticas en base de datos CIE-10.

## Características

- 🤖 **LLM Privado**: Qwen 2.5:3b-instruct ejecutado localmente vía Ollama
- 🔧 **Tool Calling**: Búsqueda automática de códigos CIE-10 mediante function calling
- 🏥 **Base de Datos CIE-10**: 14,567 códigos médicos con búsqueda full-text
- 🔒 **Privacidad**: Todos los datos permanecen en tu servidor
- 👥 **Multi-usuario**: Sistema de autenticación con sesiones y roles (usuario/admin)
- 💬 **Conversaciones**: Historial completo de chats con streaming en tiempo real
- 🎛️ **System Prompts**: Múltiples prompts configurables para diferentes especializaciones
- 📊 **Monitor del Sistema**: Panel de debug en tiempo real del flujo de Tool Calling
- 📱 **Responsive**: Interfaz moderna y adaptativa con diseño premium
- 🌓 **Dark Mode**: Diseño oscuro optimizado para uso médico
- ⚡ **Streaming**: Respuestas en tiempo real con soporte de herramientas

## Stack Tecnológico

### Frontend
- Next.js 16 (App Router) con Turbopack
- React 19
- TypeScript 5
- Tailwind CSS v4
- React Query (TanStack Query) para data fetching
- Zustand para state management
- Custom scrollbars y glassmorphism effects

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- PostgreSQL con full-text search
- Ollama API (Tool Calling con /api/chat)
- Caddy como reverse proxy
- Sistema de sesiones con cookies seguras
- Rate limiting con slowapi

### Infraestructura
- Servidor: Ubuntu 24.04 LTS
- Modelo LLM: Qwen 2.5:3b-instruct (1.9GB)
- Base de datos: PostgreSQL 16
- HTTPS con certificados SSL automáticos (Caddy)

## Instalación

### Requisitos Previos
- Python 3.12+
- Node.js 18+
- PostgreSQL 16
- Ollama con modelo qwen2.5:3b-instruct

### Setup Backend

```bash
# Clonar repositorio
git clone https://github.com/c0hete/energyapp-llm-platform.git
cd energyapp-llm-platform

# Crear entorno virtual de Python
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos PostgreSQL
createdb energyapp

# Cargar datos CIE-10 (si tienes el CSV)
python scripts/load_cie10.py data/cie10_codes.csv

# Iniciar backend
uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### Setup Frontend

```bash
cd frontend
npm install
npm run build
npm start
```

### Setup Ollama

```bash
# Instalar Ollama (si no está instalado)
curl https://ollama.ai/install.sh | sh

# Descargar modelo
ollama pull qwen2.5:3b-instruct

# Verificar que funciona
ollama run qwen2.5:3b-instruct "Hola"
```

## Desarrollo

```bash
# Frontend - Desarrollo local
npm run dev

# Build para producción
npm run build
npm start

# TypeScript check
npm run type-check
```

## Arquitectura

```
energyapp-llm-platform/
├── frontend/                     # Aplicación Next.js
│   ├── app/                     # App Router structure
│   │   ├── (auth)/              # Rutas de autenticación
│   │   └── (dashboard)/         # Rutas protegidas
│   ├── components/              # React components
│   │   ├── ChatWindow.tsx       # Chat principal con streaming
│   │   └── ToolCallingDebugPanel.tsx  # Monitor del sistema
│   ├── hooks/                   # Custom React hooks
│   │   ├── useChatStream.ts     # Hook para chat con streaming
│   │   └── useConversations.ts  # Gestión de conversaciones
│   ├── lib/                     # Utilities y API client
│   └── store/                   # Zustand stores
├── src/                         # Backend FastAPI
│   ├── main.py                  # Endpoint principal /chat con Tool Calling
│   ├── routes/                  # Rutas organizadas
│   │   ├── auth.py              # Autenticación y sesiones
│   │   ├── cie10.py             # API de códigos CIE-10
│   │   └── prompts.py           # Gestión de system prompts
│   ├── tools/                   # Tool Calling functions
│   │   ├── cie10_tools.py       # Herramientas CIE-10
│   │   └── registry.py          # Registro de tools
│   ├── ollama_client.py         # Cliente Ollama con /api/chat
│   └── models.py                # Modelos SQLAlchemy
├── docs/                        # Documentación técnica
│   ├── TOOL_CALLING_FINAL_FIX.md      # Solución completa
│   ├── TOOL_CALLING_IMPLEMENTATION.md # Implementación
│   └── CIE10_IMPLEMENTATION.md        # Base de datos CIE-10
└── static/                      # Assets estáticos
```

## Documentación

- **[TOOL_CALLING_FINAL_FIX.md](docs/TOOL_CALLING_FINAL_FIX.md)**: Solución completa y funcionamiento del Tool Calling
- **[TOOL_CALLING_IMPLEMENTATION.md](docs/TOOL_CALLING_IMPLEMENTATION.md)**: Guía técnica de implementación
- **[CIE10_IMPLEMENTATION.md](docs/CIE10_IMPLEMENTATION.md)**: Estructura de la base de datos CIE-10
- **[CONTEXT_*.md](docs/)**: Documentación detallada por componente

## Licencia

Este proyecto está licenciado bajo la licencia MIT.

**© 2025 José Alvarado Mazzei**

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## Contacto

**Autor**: José Alvarado Mazzei
**Email**: jose@alvaradomazzei.cl

---

**Versión 1.0** | 2025
