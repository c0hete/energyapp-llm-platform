# Implementación del Sistema CIE-10

## Resumen

Sistema completo de búsqueda de códigos CIE-10 (Clasificación Internacional de Enfermedades) con 14,498 códigos médicos, búsqueda full-text en español y API REST.

## Arquitectura

### Base de Datos

**Tabla: `cie10_codes`**

```sql
CREATE TABLE cie10_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,           -- Código CIE-10 (ej: "E10", "A00-B99")
    description TEXT NOT NULL,                   -- Descripción del código
    level INTEGER NOT NULL,                      -- Nivel jerárquico (0=capítulo, 1=categoría, 2=subcategoría)
    parent_code VARCHAR(10),                     -- Código padre en la jerarquía
    is_range BOOLEAN DEFAULT FALSE,              -- true si es rango (ej: "A00-B99")
    search_vector TSVECTOR,                      -- Vector de búsqueda full-text
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_cie10_code ON cie10_codes(code);
CREATE INDEX idx_cie10_search ON cie10_codes USING GIN(search_vector);
CREATE INDEX idx_cie10_category ON cie10_codes(parent_code);
CREATE INDEX idx_cie10_level ON cie10_codes(level);
```

### Estadísticas de Datos

- **Total de códigos**: 14,498
- **Rangos/categorías**: 286
- **Códigos específicos**: 14,212
- **Capítulos (level 0)**: 21
- **Categorías (level 1)**: 209
- **Subcategorías (level 2)**: 1,634

## Archivos Implementados

### 1. Modelo de Datos
**Archivo**: `src/models.py`

```python
class CIE10Code(Base):
    __tablename__ = "cie10_codes"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    code: Mapped[str] = Column(String(10), unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(Text, nullable=False)
    level: Mapped[int] = Column(Integer, nullable=False, index=True)
    parent_code: Mapped[str | None] = Column(String(10), nullable=True, index=True)
    is_range: Mapped[bool] = Column(Boolean, default=False, index=True)
    search_vector: Mapped[str | None] = Column(TSVECTOR, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
```

### 2. API Endpoints
**Archivo**: `src/routes/cie10.py`

#### GET `/cie10/search`
Buscar códigos por término

**Parámetros**:
- `q` (string, requerido): Término de búsqueda (min 2 caracteres)
- `limit` (int, opcional): Máximo de resultados (default: 10, max: 50)

**Ejemplo**:
```bash
curl "http://localhost:8001/cie10/search?q=diabetes&limit=5"
```

**Respuesta**:
```json
[
  {
    "id": 473,
    "code": "E10",
    "description": "Diabetes mellitus insulinodependiente",
    "level": 2,
    "parent_code": "E10-E14",
    "is_range": false
  }
]
```

#### GET `/cie10/{code}`
Obtener código específico

**Ejemplo**:
```bash
curl "http://localhost:8001/cie10/E10"
```

#### GET `/cie10/`
Obtener estadísticas de la base de datos

**Respuesta**:
```json
{
  "total_codes": 14498,
  "ranges": 286,
  "specific_codes": 14212,
  "levels": {
    "0": 21,
    "1": 209,
    "2": 1634
  }
}
```

### 3. Script de Carga
**Archivo**: `scripts/load_cie10.py`

Script Python para cargar códigos desde CSV a PostgreSQL.

**Uso**:
```bash
cd /root/energyapp-llm-platform
python3 scripts/load_cie10.py
```

**Funcionalidades**:
- Lee CSV con encoding UTF-8
- Detecta automáticamente códigos padre desde columnas jerárquicas
- Identifica rangos vs códigos específicos
- Crea índice full-text en español
- Muestra progreso cada 100 registros
- Maneja duplicados (ON CONFLICT)

### 4. Archivo de Datos
**Archivo**: `cie-10.csv`

**Estructura del CSV**:
```csv
code,code_0,code_1,code_2,code_3,code_4,description,level,source
A00-B99,,,,,,Ciertas enfermedades infecciosas y parasitarias,0,icdcode.info
E10,E10-E14,E00-E89,,,,"Diabetes mellitus insulinodependiente",2,icdcode.info
```

**Columnas**:
- `code`: Código CIE-10 o rango
- `code_0` a `code_4`: Jerarquía de códigos padre (se usa para detectar parent_code)
- `description`: Descripción del código
- `level`: Nivel jerárquico (0=capítulo, 1=categoría, 2=subcategoría, etc.)
- `source`: Origen de los datos

## Búsqueda Full-Text

### Configuración PostgreSQL

El sistema usa `to_tsvector` y `to_tsquery` de PostgreSQL con diccionario español:

```sql
-- Actualizar vectores de búsqueda
UPDATE cie10_codes
SET search_vector = to_tsvector('spanish', code || ' ' || description);

-- Búsqueda
SELECT * FROM cie10_codes
WHERE search_vector @@ plainto_tsquery('spanish', 'diabetes');
```

### Comportamiento de Búsqueda

1. **Búsqueda por código**: Si el término empieza con letra o contiene números
   - Busca en campo `code` (case-insensitive)
   - También busca en descripción vía full-text

2. **Búsqueda por descripción**: Si el término es solo texto
   - Usa full-text search en español
   - Stemming automático (ej: "diabético" encuentra "diabetes")

3. **Ordenamiento**:
   - Prioriza códigos específicos sobre rangos (`is_range=false` primero)
   - Luego ordena alfabéticamente por código

## Integración con Qwen

### Opción 1: System Prompt con Instrucciones (Recomendado)

Esta es la forma más sencilla de integrar CIE-10 con Qwen. Agregar estas instrucciones al system prompt del modelo.

#### Configuración en la Base de Datos

En la tabla `system_prompts`, crear o actualizar el prompt para incluir:

```sql
INSERT INTO system_prompts (name, description, content, is_default, is_active, created_by)
VALUES (
  'Asistente Médico CIE-10',
  'Prompt para asistencia médica con acceso a códigos CIE-10',
  'Eres un asistente médico especializado. Tienes acceso a una base de datos completa de códigos CIE-10 (Clasificación Internacional de Enfermedades).

IMPORTANTE: Cuando el usuario pregunte por códigos médicos, diagnósticos o enfermedades, DEBES buscar en la base de datos CIE-10 antes de responder.

Para buscar códigos CIE-10:
1. Usa el endpoint interno: GET http://localhost:8001/cie10/search?q=<término>&limit=<número>
2. También puedes obtener un código específico: GET http://localhost:8001/cie10/<código>

Ejemplos de uso:
- Usuario pregunta por "diabetes" → Buscar: http://localhost:8001/cie10/search?q=diabetes&limit=5
- Usuario pregunta por "hipertensión arterial" → Buscar: http://localhost:8001/cie10/search?q=hipertension
- Usuario menciona código "E10" → Verificar: http://localhost:8001/cie10/E10

FORMATO DE RESPUESTA:
Cuando encuentres códigos CIE-10 relevantes, presenta la información así:

📋 **Código CIE-10**: E10
📝 **Descripción**: Diabetes mellitus insulinodependiente
🏷️ **Categoría**: E10-E14 (Diabetes mellitus)

Códigos relacionados:
- E10.0: Con coma
- E10.1: Con cetoacidosis
- E10.2: Con complicaciones renales

REGLAS:
- Siempre verifica la ortografía del término médico antes de buscar
- Si no encuentras resultados, sugiere términos alternativos
- Explica brevemente la condición médica además de dar el código
- Menciona si el código es un rango (categoría) o código específico',
  true,
  true,
  1  -- ID del admin que lo crea
);
```

#### Uso en el Frontend

Cuando el usuario inicie una conversación, seleccionar el prompt "Asistente Médico CIE-10" desde el dropdown de prompts.

**Archivo**: `static/index.html` o componente React de chat

```javascript
// Al enviar mensaje, incluir el prompt_id
const response = await fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionToken}`
  },
  body: JSON.stringify({
    prompt: userMessage,
    conversation_id: currentConversationId,
    prompt_id: selectedPromptId  // ID del prompt CIE-10
  })
});
```

### Opción 2: Función/Tool Calling (Futuro)

Si Qwen soporta function calling (como GPT-4), definir herramientas:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "search_cie10",
        "description": "Busca códigos CIE-10 por término médico en español. Retorna códigos y descripciones relevantes.",
        "parameters": {
          "type": "object",
          "properties": {
            "q": {
              "type": "string",
              "description": "Término de búsqueda médico (enfermedad, síntoma, diagnóstico)"
            },
            "limit": {
              "type": "integer",
              "description": "Número máximo de resultados a retornar",
              "default": 10,
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": ["q"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_cie10_code",
        "description": "Obtiene información detallada de un código CIE-10 específico",
        "parameters": {
          "type": "object",
          "properties": {
            "code": {
              "type": "string",
              "description": "Código CIE-10 exacto (ej: E10, I10, A00)"
            }
          },
          "required": ["code"]
        }
      }
    }
  ]
}
```

**Implementación del handler**:

```python
# En src/ollama_client.py o nuevo archivo src/tools/cie10_tools.py
import httpx

async def handle_cie10_search(q: str, limit: int = 10) -> dict:
    """Handler para la función search_cie10"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8001/cie10/search",
            params={"q": q, "limit": limit}
        )
        return response.json()

async def handle_get_cie10_code(code: str) -> dict:
    """Handler para la función get_cie10_code"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8001/cie10/{code}")
        return response.json()
```

### Ejemplos de Conversaciones con Qwen

#### Ejemplo 1: Búsqueda Simple

**Usuario**: ¿Qué código CIE-10 corresponde a diabetes tipo 1?

**Qwen** (con system prompt):
```
Voy a buscar el código CIE-10 para diabetes tipo 1...

[Realiza búsqueda interna: GET /cie10/search?q=diabetes%20tipo%201]

📋 **Código CIE-10**: E10
📝 **Descripción**: Diabetes mellitus insulinodependiente
🏷️ **Categoría**: E10-E14 (Diabetes mellitus)

Este es el código estándar para diabetes tipo 1 (insulinodependiente). La diabetes tipo 1 es una condición en la que el páncreas produce poca o ninguna insulina.

Códigos específicos según complicaciones:
- **E10.0**: Con coma
- **E10.1**: Con cetoacidosis
- **E10.2**: Con complicaciones renales
- **E10.3**: Con complicaciones oftálmicas
- **E10.4**: Con complicaciones neurológicas
- **E10.5**: Con complicaciones circulatorias periféricas
```

#### Ejemplo 2: Múltiples Resultados

**Usuario**: Necesito los códigos para hipertensión

**Qwen**:
```
Buscando códigos CIE-10 para hipertensión...

[Búsqueda: GET /cie10/search?q=hipertension&limit=10]

Encontré varios códigos relacionados con hipertensión:

📋 **Código I10**
📝 Hipertensión esencial (primaria)
- Este es el código más común para hipertensión arterial sin causa identificable

📋 **Código I11**
📝 Enfermedad cardíaca hipertensiva
- Hipertensión que afecta el corazón

📋 **Código I12**
📝 Enfermedad renal hipertensiva
- Hipertensión que afecta los riñones

📋 **Código I13**
📝 Enfermedad cardíaca y renal hipertensiva
- Hipertensión que afecta corazón y riñones

📋 **Código I15**
📝 Hipertensión secundaria
- Hipertensión causada por otra condición médica

¿Necesitas información más específica sobre alguno de estos códigos?
```

#### Ejemplo 3: Código No Encontrado

**Usuario**: ¿Cuál es el código para "gripe común"?

**Qwen**:
```
Buscando código CIE-10 para gripe común...

[Búsqueda: GET /cie10/search?q=gripe%20comun]

Encontré estos códigos relacionados con gripe e infecciones respiratorias:

📋 **Código J11**
📝 Influenza debida a virus no identificado
- Este es el código para gripe común cuando no se ha identificado el virus específico

📋 **Código J10**
📝 Influenza debida a virus de la influenza identificado
- Para casos donde se ha confirmado el tipo de virus

También encontré:
📋 **Código J00** - Rinofaringitis aguda (resfriado común)
📋 **Código J06.9** - Infección aguda de las vías respiratorias superiores

Nota: La "gripe común" puede referirse a influenza (J11) o al resfriado común (J00), dependiendo del contexto clínico.
```

### Configuración Técnica en Ollama

Si estás usando Ollama localmente, crear un Modelfile personalizado:

```dockerfile
# Modelfile para Qwen con CIE-10
FROM qwen2.5:7b

# System prompt con integración CIE-10
SYSTEM """
Eres un asistente médico especializado con acceso a la base de datos CIE-10.

Tienes acceso a estos endpoints internos:
- GET http://localhost:8001/cie10/search?q=<término>&limit=<número>
- GET http://localhost:8001/cie10/<código>

IMPORTANTE: Cuando el usuario pregunte por códigos médicos, diagnósticos o enfermedades, busca en CIE-10 antes de responder.

Formato de respuesta:
📋 Código CIE-10: <código>
📝 Descripción: <descripción>
🏷️ Categoría: <categoría padre>

Siempre explica brevemente la condición médica además del código.
"""

# Parámetros optimizados para respuestas médicas
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER top_k 40
```

**Crear el modelo**:
```bash
ollama create qwen-cie10 -f Modelfile
```

**Usar el modelo**:
```python
# En src/config.py
class Settings(BaseSettings):
    ollama_model: str = Field(default="qwen-cie10", env="OLLAMA_MODEL")
```

## Deployment

### Paso 1: Crear Tabla en Producción

```bash
ssh root@servidor
cd /root/energyapp-llm-platform

python3 -c "
from src.db import engine
from src.models import Base
Base.metadata.tables['cie10_codes'].create(engine, checkfirst=True)
"
```

### Paso 2: Cargar Datos

```bash
python3 scripts/load_cie10.py
```

Tiempo aproximado: ~30 segundos para 14,498 registros

### Paso 3: Reiniciar Backend

```bash
kill -9 $(pgrep -f uvicorn)
cd /root/energyapp-llm-platform
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8001 > /var/log/fastapi.log 2>&1 &
```

### Paso 4: Verificar

```bash
curl "http://localhost:8001/cie10/"
curl "http://localhost:8001/cie10/search?q=diabetes&limit=3"
```

## Mantenimiento

### Actualizar Códigos CIE-10

Si hay una nueva versión del CIE-10:

1. Reemplazar archivo `cie-10.csv`
2. Truncar tabla: `TRUNCATE TABLE cie10_codes;`
3. Recargar: `python3 scripts/load_cie10.py`

### Backup

```bash
# Backup de datos
pg_dump -U energyapp -t cie10_codes energyapp > cie10_backup.sql

# Restore
psql -U energyapp energyapp < cie10_backup.sql
```

## Rendimiento

- **Búsqueda**: ~5-10ms (con índice GIN)
- **Carga inicial**: ~30 segundos
- **Espacio en disco**: ~2.5MB de datos + ~1MB de índices

## Próximos Pasos

1. **Agregar jerarquía navegable**: Endpoint para obtener hijos de un código
2. **Caché**: Redis para búsquedas frecuentes
3. **Autocompletar**: Endpoint para sugerencias mientras el usuario escribe
4. **Sinónimos**: Tabla de sinónimos médicos comunes
5. **Exportar**: Generar reportes con códigos usados

## Referencias

- CIE-10 oficial: https://www.who.int/standards/classifications/classification-of-diseases
- PostgreSQL Full-Text Search: https://www.postgresql.org/docs/current/textsearch.html
- Datos fuente: icdcode.info
