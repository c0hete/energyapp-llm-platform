# 🚀 INSTRUCCIONES DE DESPLIEGUE - FASE 0 PRODUCCIÓN

**Última actualización:** 2025-12-02
**Commit:** b15c971
**Status:** ✅ Listo para desplegar

---

## 📋 Resumen

Tienes 2 opciones para desplegar:
- **Opción A (Recomendada):** Script automatizado (2 minutos)
- **Opción B (Manual):** Paso a paso (5 minutos)

---

## Opción A: Script Automatizado (RECOMENDADO)

### Paso 1: En tu máquina local
```bash
cd c:\Users\JoseA\energyapp-llm-platform

# Obtener últimos cambios
git pull origin main

# Copiar script de despliegue al VPS
scp deploy/setup-production.sh josealmsd@energyapp.alvaradomazzei.cl:/root/energyapp-llm-platform/
```

### Paso 2: En el VPS (SSH)
```bash
# Conectar al VPS
ssh josealmsd@energyapp.alvaradomazzei.cl

# Navegar al directorio
cd /root/energyapp-llm-platform

# Dar permisos de ejecución
chmod +x deploy/setup-production.sh

# Ejecutar script
./deploy/setup-production.sh
```

**Eso es todo.** El script hace:
1. ✅ Git pull automático
2. ✅ Instala systemd service para Next.js
3. ✅ Actualiza configuración de Caddy
4. ✅ Valida y recarga servicios
5. ✅ Verifica salud de todos los componentes

---

## Opción B: Despliegue Manual (si algo falla)

### Paso 1: Obtener cambios en VPS
```bash
ssh josealmsd@energyapp.alvaradomazzei.cl
cd /root/energyapp-llm-platform
git pull origin main
```

### Paso 2: Instalar Next.js Service
```bash
# Copiar archivo de servicio a systemd
sudo cp deploy/energyapp-web.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/energyapp-web.service

# Recargar daemon y habilitar
sudo systemctl daemon-reload
sudo systemctl enable energyapp-web
sudo systemctl start energyapp-web

# Verificar que esté corriendo
sudo systemctl status energyapp-web
```

### Paso 3: Actualizar Caddy
```bash
# Backup de configuración actual
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup

# Copiar nueva configuración
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile

# Validar sintaxis
sudo caddy validate --config /etc/caddy/Caddyfile

# Recargar (sin downtime)
sudo systemctl reload caddy

# Verificar
sudo systemctl status caddy
```

### Paso 4: Verificar que todo funciona
```bash
# FastAPI health
curl http://127.0.0.1:8001/health

# Next.js (esperar 3 segundos)
sleep 3
curl http://127.0.0.1:3000

# Via HTTPS (desde tu máquina, NO en el VPS)
curl -I https://energyapp.alvaradomazzei.cl/login
```

---

## 🔍 Solución de Problemas

### ❌ "Next.js no inicia"
```bash
# Ver logs detallados
sudo journalctl -u energyapp-web -n 50 --no-pager

# Probar manualmente
cd /root/energyapp-llm-platform/frontend
npm run start
```

### ❌ "Caddy falla al recargar"
```bash
# Ver errores de sintaxis
sudo caddy validate --config /etc/caddy/Caddyfile

# Ver logs
sudo journalctl -u caddy -n 50 --no-pager

# Si es crítico, revertir backup
sudo cp /etc/caddy/Caddyfile.backup /etc/caddy/Caddyfile
sudo systemctl restart caddy
```

### ❌ "Conexión rechazada en /api/*"
```bash
# Verificar que FastAPI está corriendo
curl http://127.0.0.1:8001/health

# Verificar puertos abiertos
sudo netstat -tlpn | grep -E ':(3000|8001)'

# Ver logs de Caddy
sudo journalctl -u caddy -f
```

### ❌ "Error: ENOENT: no such file or directory"
```bash
# Asegurarse que los archivos existen
ls -la /root/energyapp-llm-platform/deploy/
ls -la /etc/systemd/system/energyapp-web.service
ls -la /etc/caddy/Caddyfile

# Si faltan, copiarlos de nuevo
scp deploy/energyapp-web.service josealmsd@energyapp.alvaradomazzei.cl:/tmp/
scp deploy/Caddyfile josealmsd@energyapp.alvaradomazzei.cl:/tmp/
# Luego copiar en VPS con sudo
```

---

## 📊 Verificación Post-Despliegue

Después de ejecutar el script, verifica:

```bash
# 1. Servicios activos
sudo systemctl status energyapp-web
sudo systemctl status caddy

# 2. Ports escuchando
sudo netstat -tlpn | grep -E ":(3000|8001)"

# 3. Logs en tiempo real (en 2 terminales separadas)
# Terminal 1:
sudo journalctl -u energyapp-web -f

# Terminal 2:
sudo journalctl -u caddy -f

# 4. Test de conectividad (desde tu máquina)
curl -v https://energyapp.alvaradomazzei.cl/login
```

---

## 📁 Archivos Utilizados

| Archivo | Función |
|---------|---------|
| `deploy/setup-production.sh` | Script automatizado (EJECUTA ESTO) |
| `deploy/energyapp-web.service` | Systemd service para Next.js |
| `deploy/Caddyfile` | Configuración de proxy inverso |
| `deploy/DEPLOY.md` | Guía completa (referencia) |
| `DEPLOY_QUICK_START.md` | Referencia rápida |

---

## 🎯 Qué hace el despliegue

```
Flujo de Despliegue:
┌─────────────────────────────────────────────────────┐
│                    Tu máquina                       │
│  (git pull + scp setup-production.sh)               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                      VPS                            │
│                                                      │
│  1. git pull origin main                            │
│     └─ Descarga deploy/ files                       │
│                                                      │
│  2. sudo cp deploy/energyapp-web.service →          │
│     /etc/systemd/system/                            │
│     └─ Registra systemd service                     │
│                                                      │
│  3. sudo systemctl enable energyapp-web             │
│     └─ Inicia automáticamente en boot               │
│                                                      │
│  4. sudo cp deploy/Caddyfile → /etc/caddy/          │
│     └─ Reemplaza config anterior                    │
│                                                      │
│  5. sudo systemctl reload caddy                     │
│     └─ Recarga sin downtime                         │
│                                                      │
│  ✅ RESULTADO:                                       │
│     - Next.js corre en puerto 3000                  │
│     - Caddy proxies / → 3000, /api/* → 8001        │
│     - HTTPS en energyapp.alvaradomazzei.cl          │
└─────────────────────────────────────────────────────┘
```

---

## ⏱️ Tiempo estimado

- Opción A (Script): **2-3 minutos**
- Opción B (Manual): **5-7 minutos**
- Verificación: **1 minuto**

**Total: ~5 minutos de downtime (solo mientras Caddy recarga)**

---

## ✅ Checklist Final

Antes de considerar completado:

- [ ] Script ejecutado sin errores (o pasos manuales completados)
- [ ] `sudo systemctl status energyapp-web` muestra "active (running)"
- [ ] `sudo systemctl status caddy` muestra "active (running)"
- [ ] `curl http://127.0.0.1:8001/health` retorna {"status": "ok"}
- [ ] `curl http://127.0.0.1:3000` retorna HTML de Next.js
- [ ] `curl -I https://energyapp.alvaradomazzei.cl/login` retorna 200
- [ ] Logs sin errores: `sudo journalctl -u energyapp-web -n 20`

---

## 🆘 ¿Algo no funciona?

Si encuentras problemas:

1. **Lee los logs:** `sudo journalctl -u energyapp-web -f`
2. **Verifica configuración:** `cat /etc/systemd/system/energyapp-web.service`
3. **Valida Caddy:** `sudo caddy validate --config /etc/caddy/Caddyfile`
4. **Revierte cambios:** `sudo systemctl stop energyapp-web && sudo cp /etc/caddy/Caddyfile.backup /etc/caddy/Caddyfile && sudo systemctl restart caddy`

---

**Versión:** FASE 0 - Next.js 14 Production Deployment
**Última actualización:** 2025-12-02
**Autor:** Claude Code

**¿Listo?** Ejecuta el script y espera el ✅ final.
