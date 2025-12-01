# Arquitectura y despliegue

## Visión general
- **Objetivo**: Plataforma LLM privada para EnergyApp, con inferencia local mediante Ollama (Qwen 2.5:3B).
- **Modo operativo**: API/servicio interno que otras apps (Laravel, Node.js) consumen.
- **Entorno de producción**: Ubuntu 24.04, 6 vCPU, ~12 GB RAM, disco 100 GB.

## Componentes
- **Ollama**: Sirve el modelo en `127.0.0.1:11434`.
- **Aplicación LLM** (este repo): clientes, pipelines, endpoints y orquestación.
- **Servicios existentes**: Caddy/Apache como reverse proxy, Docker (Nextcloud), PostgreSQL 16.
- **Seguridad**: Fail2Ban + UFW; WireGuard abierto en 51820/udp para VPN.

## Estructura de carpetas (repo)
- `src/`: código fuente de la app (API, clientes, pipelines).
- `config/`: `settings.yaml` y variables sensibles (usar `.env`).
- `data/`: artefactos locales (embeddings, caches). Evitar commitear datos pesados.
- `tests/`: pruebas unitarias/integración.
- `docs/`: documentación (esta carpeta).
- `scripts/`: utilidades de desarrollo/despliegue.

## Flujo de despliegue recomendado
1. Trabajo local: commits y push a GitHub.
2. En el VPS: `git pull` en `/srv/ai/ia-empresas`.
3. Crear/actualizar entorno virtual y dependencias.
4. Ejecutar tests básicos.
5. Arrancar servicio/API (por definir: uvicorn, gunicorn, etc.).

## Integración con Ollama
- Endpoint: `http://127.0.0.1:11434`.
- Modelo inicial: `qwen2.5:3b-instruct`.
- Mantener los requests en LAN/localhost; no exponer Ollama públicamente.

## Configuración (settings.yaml)
Ejemplo mínimo:
```yaml
app:
  name: energyapp-llm
  env: dev

ollama:
  host: http://127.0.0.1:11434
  model: qwen2.5:3b-instruct
  temperature: 0.6
  top_p: 0.9

logging:
  level: INFO
  file: ./logs/app.log
```

## Próximos pasos sugeridos
- Definir el framework (FastAPI/Flask) y esqueleto del servicio.
- Añadir `requirements.txt` y flujo de instalación.
- Escribir un cliente mínimo contra Ollama (ping + generación).
- Agregar pipeline de pruebas (pytest) y script de arranque.
