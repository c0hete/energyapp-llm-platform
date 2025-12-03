# EnergyApp

**Chat LLM privado con Qwen 2.5·3B**

Una plataforma de chat basada en LLM ejecutado localmente con privacidad de datos garantizada. Construida con Next.js 16, TypeScript y Tailwind CSS.

## Características

- 🤖 **LLM Privado**: Qwen 2.5·3B ejecutado localmente vía Ollama
- 🔒 **Privacidad**: Todos los datos permanecen en tu servidor
- 👥 **Multi-usuario**: Sistema de autenticación y roles (usuario/admin)
- 💬 **Conversaciones**: Historial completo de chats con soporte para múltiples conversaciones
- 🎛️ **System Prompts**: Configura prompts del sistema para diferentes casos de uso
- 📱 **Responsive**: Interfaz moderna y adaptativa con Tailwind CSS
- 🌓 **Dark Mode**: Diseño oscuro optimizado para la lectura
- ⚡ **Tipado**: TypeScript en frontend y backend

## Stack Tecnológico

### Frontend
- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS
- React Query (TanStack Query)
- Zustand (state management)

### Backend
- Next.js API Routes
- Node.js
- TypeScript
- PostgreSQL
- Ollama (LLM inference)

## Instalación

### Requisitos previos
- Node.js 18+
- PostgreSQL
- Ollama con modelo Qwen 2.5·3B

### Setup

```bash
# Clonar repositorio
git clone https://github.com/c0hete/energyapp-llm-platform.git
cd energyapp-llm-platform

# Frontend
cd frontend
npm install
npm run dev

# Backend (si es necesario)
cd ../backend
npm install
npm run dev
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
├── frontend/                 # Aplicación Next.js
│   ├── app/                 # App Router structure
│   ├── components/          # React components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utilities y helpers
│   ├── store/               # Zustand stores
│   └── styles/              # Global styles
├── backend/                 # Backend (si aplica)
└── docs/                    # Documentación adicional
```

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
