README.md — versión profesional
# EnergyApp LLM Platform

Plataforma de Inteligencia Artificial self-hosted para EnergyApp, basada en modelos ligeros Qwen 2.5:3B utilizando Ollama. Diseñada como proyecto educacional y de infraestructura privada.

##  Características
- IA completamente local (privada) usando Ollama
- Optimizada para servidores con 8–12GB RAM
- Estructura modular para integrarse con aplicaciones Laravel o Node.js
- Proyecto educacional enfocado en despliegue real en VPS

##  Modelo Actual
- **Qwen 2.5:3B Instruct**  
- Cuantización: Q4  
- Consumo aproximado: 2–3GB RAM en inferencia

##  Estructura del Proyecto


src/ → código fuente
config/ → settings de la plataforma
data/ → archivos, embeddings, etc.
tests/ → tests unitarios
docs/ → documentación
scripts/ → scripts utilitarios


##  Requisitos
- Python 3.10+
- Ollama instalado
- Ubuntu 24.04 (producción)
- VPS 12GB RAM recomendado

##  Autor
José Alvarado Mazzei – 2025  
MIT License