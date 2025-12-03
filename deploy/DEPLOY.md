# Guía de Despliegue en Producción

**Versión:** FASE 0
**Fecha:** 2025-12-02
**Estado:** VPS listo para producción

## Prerequisitos

- ✅ Frontend compilado en VPS (`/root/energyapp-llm-platform/frontend/.next`)
- ✅ FastAPI corriendo en puerto 8001
- ✅ Node.js v20.19.6 y npm 10.8.2 instalados
- ✅ Caddy instalado en VPS

## Pasos de Despliegue

### 1. Copiar archivos de configuración al VPS

```bash
# En tu máquina local
scp deploy/energyapp-web.service josealmsd@energyapp.alvaradomazzei.cl:/tmp/
scp deploy/Caddyfile josealmsd@energyapp.alvaradomazzei.cl:/tmp/
```

### 2. En el VPS: Instalar systemd service para Next.js

```bash
# SSH al VPS
ssh josealmsd@energyapp.alvaradomazzei.cl

# Copiar archivo de servicio
sudo cp /tmp/energyapp-web.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/energyapp-web.service

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar y iniciar el servicio
sudo systemctl enable energyapp-web
sudo systemctl start energyapp-web

# Verificar estado
sudo systemctl status energyapp-web
sudo journalctl -u energyapp-web -f  # Ver logs en tiempo real
```

### 3. En el VPS: Actualizar configuración de Caddy

```bash
# Backup de la configuración actual
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup

# Copiar nueva configuración
sudo cp /tmp/Caddyfile /etc/caddy/Caddyfile
sudo chmod 644 /etc/caddy/Caddyfile

# Validar sintaxis
sudo caddy validate --config /etc/caddy/Caddyfile

# Recargar Caddy sin tiempo de inactividad
sudo systemctl reload caddy

# Verificar estado
sudo systemctl status caddy
```

### 4. Verificar despliegue

```bash
# Health check local
curl http://127.0.0.1:8001/health          # FastAPI
curl http://127.0.0.1:3000                 # Next.js

# Via Caddy (desde tu máquina)
curl https://energyapp.alvaradomazzei.cl/login

# Logs
sudo journalctl -u energyapp-web -f
sudo journalctl -u caddy -f
sudo tail -f /var/log/caddy/energyapp-access.log
```

## Solución de Problemas

### Next.js no inicia
```bash
sudo journalctl -u energyapp-web -n 50
cd /root/energyapp-llm-platform/frontend
npm run start  # Verificar manualmente
```

### Caddy falla al recargar
```bash
sudo caddy validate --config /etc/caddy/Caddyfile
# Ver errores de sintaxis
sudo systemctl restart caddy  # O forzar reinicio si es necesario
```

### Conexión rechazada a API
- Verificar que FastAPI esté corriendo: `curl http://127.0.0.1:8001/health`
- Verificar puerto 3000: `sudo netstat -tlpn | grep :3000`
- Ver logs de Caddy: `sudo journalctl -u caddy -f`

## Scripts para Actualizar (después de git push)

### Script: `update-vps.sh`
```bash
#!/bin/bash
cd /root/energyapp-llm-platform

# Frontend
cd frontend
npm install
npm run build
cd ..

# Reiniciar servicios
sudo systemctl restart energyapp-web

# Verificar
sudo systemctl status energyapp-web

echo "✅ Frontend actualizado"
```

### Ejecutar en el VPS
```bash
chmod +x update-vps.sh
./update-vps.sh
```

## Descripción de Archivos

- **energyapp-web.service**: Systemd service para Next.js (puerto 3000)
- **Caddyfile**: Configuración de Caddy con proxy a Next.js + FastAPI
- **DEPLOY.md**: Esta guía de despliegue

## Siguiente Fase

- FASE 1: Mejorar UI de login y register
- FASE 2: Implementar chat con streaming + lista de conversaciones
- FASE 3: Panel admin interactivo
- FASE 4: System Prompt Manager
- FASE 5: CSRF Protection + Rate limiting

---

**Estado**: 🟢 Listo para despliegue
**Build**: `/root/energyapp-llm-platform/frontend/.next` (8.1M)
**Commit**: 028ffcd (PHASE 0: Set up Next.js 14 with React Query + Zustand + Middleware)
