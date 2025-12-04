#!/bin/bash

# Script para desplegar Tool Calling a producción
# Autor: Claude Code
# Fecha: Diciembre 2024

SERVER="root@184.174.33.249"
PROJECT_DIR="/root/energyapp-llm-platform"

echo "=================================="
echo "DESPLIEGUE DE TOOL CALLING"
echo "=================================="
echo ""

# Paso 1: Copiar archivos del módulo tools
echo "1. Copiando módulo tools al servidor..."
scp -r src/tools $SERVER:$PROJECT_DIR/src/
echo "   ✓ Módulo tools copiado"
echo ""

# Paso 2: Copiar ollama_client.py modificado
echo "2. Copiando ollama_client.py modificado..."
scp src/ollama_client.py $SERVER:$PROJECT_DIR/src/
echo "   ✓ ollama_client.py actualizado"
echo ""

# Paso 3: Copiar main.py modificado
echo "3. Copiando main.py modificado..."
scp src/main.py $SERVER:$PROJECT_DIR/src/
echo "   ✓ main.py actualizado"
echo ""

# Paso 4: Copiar script SQL
echo "4. Copiando script SQL..."
scp scripts/insert_tool_calling_prompt.sql $SERVER:$PROJECT_DIR/scripts/
echo "   ✓ Script SQL copiado"
echo ""

# Paso 5: Insertar system prompt en la base de datos
echo "5. Insertando system prompt en la base de datos..."
ssh $SERVER "cd $PROJECT_DIR && python3 << 'PYTHON_EOF'
from src.db import SessionLocal
from src.config import get_settings

settings = get_settings()
db = SessionLocal()

# Leer y ejecutar el SQL
with open('scripts/insert_tool_calling_prompt.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    # Ejecutar SQL (quitando el INSERT si ya existe)
    try:
        db.execute(sql)
        db.commit()
        print('   ✓ System prompt insertado correctamente')
    except Exception as e:
        if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
            print('   ⚠ System prompt ya existe (omitiendo)')
        else:
            print(f'   ✗ Error: {e}')
            raise
    finally:
        db.close()
PYTHON_EOF
"
echo ""

# Paso 6: Reiniciar backend
echo "6. Reiniciando backend..."
ssh $SERVER "ps aux | grep 'uvicorn.*src.main:app' | grep -v grep | awk '{print \$2}' | xargs -r kill -9"
sleep 2
ssh $SERVER "cd $PROJECT_DIR && nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8001 > /var/log/fastapi.log 2>&1 &"
sleep 5
echo "   ✓ Backend reiniciado"
echo ""

# Paso 7: Verificar que el backend está funcionando
echo "7. Verificando backend..."
HEALTH=$(ssh $SERVER "curl -s http://localhost:8001/health")
if [[ $HEALTH == *"status"* ]]; then
    echo "   ✓ Backend respondiendo correctamente"
else
    echo "   ✗ Backend no responde correctamente"
    echo "   Respuesta: $HEALTH"
    exit 1
fi
echo ""

# Paso 8: Verificar endpoint CIE-10
echo "8. Verificando endpoint CIE-10..."
CIE10_RESP=$(ssh $SERVER "curl -s http://localhost:8001/cie10/")
if [[ $CIE10_RESP == *"total_codes"* ]]; then
    echo "   ✓ Endpoint CIE-10 funcionando"
else
    echo "   ✗ Endpoint CIE-10 no responde"
    echo "   Respuesta: $CIE10_RESP"
fi
echo ""

echo "=================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "=================================="
echo ""
echo "Próximos pasos:"
echo "1. Acceder a la interfaz web"
echo "2. Seleccionar el prompt 'Asistente Médico CIE-10 (Tool Calling)'"
echo "3. Probar con preguntas médicas:"
echo "   - '¿Cuál es el código para diabetes tipo 1?'"
echo "   - 'Busca códigos de hipertensión'"
echo "   - '¿Qué es el código E10?'"
echo ""
echo "Para ver logs del backend:"
echo "   ssh $SERVER 'tail -f /var/log/fastapi.log'"
echo ""
