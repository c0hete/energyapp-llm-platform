# EnergyApp LLM Platform

Plataforma de IA auto hospedada para EnergyApp, basada en modelos ligeros (Qwen 2.5:3B vía Ollama). Pensada como referencia educativa y como base para despliegue privado en VPS.

## Características
- IA 100 % local con Ollama (sin datos externos).
- Optimizada para servidores modestos (8-12 GB RAM).
- Estructura modular que puede integrarse con Laravel, Node.js u otros backends.
- Documentación y scripts de despliegue pensados para VPS Ubuntu 24.04.

## Modelo actual
- **Modelo**: Qwen 2.5:3B Instruct
- **Cuantización**: Q4
- **Consumo esperado**: ~2-3 GB RAM durante inferencia

## Estructura del proyecto
- `src/` — código fuente de la app y clientes.
- `config/` — configuración (YAML/ENV).
- `data/` — artefactos, embeddings, descargas de modelos.
- `tests/` — pruebas unitarias/integración.
- `docs/` — documentación de arquitectura y operación.
- `scripts/` — utilidades para desarrollo/despliegue.

## Requisitos (local)
- Python 3.10+
- Bash (para `scripts/run_local.sh`)
- (Opcional) Ollama local si quieres probar inferencias en tu máquina

## Entorno de producción (referencia)
- Ubuntu 24.04 LTS
- 6 vCPU / ~12 GB RAM / 100 GB SSD
- Ollama escuchando en `127.0.0.1:11434` con Qwen 2.5:3B

## Primeros pasos
1) Crear y activar un entorno virtual
```
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
```
2) Instalar dependencias (cuando agreguemos `requirements.txt`)
```
pip install -r requirements.txt
```
3) Ejecutar pruebas rápidas
```
python -m pytest
```
4) Configurar credenciales y endpoints en `config/settings.yaml`.

## Autoría
- José Alvarado Mazzei — 2025
- Licencia: MIT
