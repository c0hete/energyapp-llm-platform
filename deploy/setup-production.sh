#!/bin/bash

# ============================================================
# SETUP PRODUCCIÓN - EnergyApp Next.js + Caddy
# ============================================================
# Script automatizado para desplegar FASE 0 en VPS
# Ejecutar en: /root/energyapp-llm-platform
# ============================================================

set -e  # Exit on error

echo "🚀 Iniciando despliegue de producción..."

# ============================================================
# 1. Obtener últimos cambios
# ============================================================
echo ""
echo "📥 Paso 1: Obtener últimos cambios de GitHub..."
cd /root/energyapp-llm-platform
git pull origin main

# ============================================================
# 2. Instalar Next.js service
# ============================================================
echo ""
echo "🔧 Paso 2: Instalar systemd service para Next.js..."

# Copiar archivo de servicio
sudo cp deploy/energyapp-web.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/energyapp-web.service

# Recargar systemd daemon
sudo systemctl daemon-reload

# Habilitar servicio (iniciar al arrancar)
sudo systemctl enable energyapp-web

# Iniciar servicio
sudo systemctl start energyapp-web

echo "✅ Systemd service instalado"
sudo systemctl status energyapp-web --no-pager

# ============================================================
# 3. Actualizar configuración de Caddy
# ============================================================
echo ""
echo "🔧 Paso 3: Actualizar configuración de Caddy..."

# Backup de la configuración actual
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup.$(date +%s)
echo "   📦 Backup creado"

# Copiar nueva configuración
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile

# Validar sintaxis
if sudo caddy validate --config /etc/caddy/Caddyfile > /dev/null 2>&1; then
    echo "   ✅ Sintaxis de Caddy válida"
else
    echo "   ❌ Error en configuración de Caddy"
    exit 1
fi

# Recargar Caddy sin tiempo de inactividad
sudo systemctl reload caddy

echo "✅ Caddy actualizado"
sudo systemctl status caddy --no-pager

# ============================================================
# 4. Verificaciones de salud
# ============================================================
echo ""
echo "🏥 Paso 4: Verificaciones de salud..."

echo ""
echo "   📍 Verificando FastAPI (puerto 8001)..."
if curl -s http://127.0.0.1:8001/health > /dev/null 2>&1; then
    echo "   ✅ FastAPI respondiendo"
else
    echo "   ⚠️  FastAPI no responde en puerto 8001"
fi

echo ""
echo "   📍 Verificando Next.js (puerto 3000)..."
sleep 2  # Dar tiempo a Next.js para iniciar
if curl -s http://127.0.0.1:3000 > /dev/null 2>&1; then
    echo "   ✅ Next.js respondiendo"
else
    echo "   ⚠️  Next.js puede estar iniciando (ver logs)"
fi

# ============================================================
# 5. Resumen
# ============================================================
echo ""
echo "✨ =========================================="
echo "  DESPLIEGUE COMPLETADO"
echo "=========================================="
echo ""
echo "📊 Estado de servicios:"
sudo systemctl status energyapp-web --no-pager | grep "Active:" || true
sudo systemctl status caddy --no-pager | grep "Active:" || true
echo ""
echo "🔗 URLs:"
echo "   - https://energyapp.alvaradomazzei.cl/login (via HTTPS)"
echo "   - http://127.0.0.1:3000 (local Next.js)"
echo "   - http://127.0.0.1:8001/health (FastAPI health)"
echo ""
echo "📋 Próximos pasos:"
echo "   - Ver logs: sudo journalctl -u energyapp-web -f"
echo "   - Ver logs Caddy: sudo journalctl -u caddy -f"
echo "   - Probar: curl -I https://energyapp.alvaradomazzei.cl/login"
echo ""
echo "✅ Listo para producción"
