# Sistema de Carga de Datos CSV

Este documento resume la nueva funcionalidad de carga de archivos CSV internos para consulta mediante API REST y uso con Qwen.

## Documentos Disponibles

1. **[CIE10_IMPLEMENTATION.md](CIE10_IMPLEMENTATION.md)** - Implementación completa del sistema CIE-10 (14,498 códigos médicos)
2. **[CSV_LOADING_GUIDE.md](CSV_LOADING_GUIDE.md)** - Guía genérica para cargar cualquier CSV interno

## ¿Qué Ofrece Esta Funcionalidad?

### Para Desarrolladores
- Sistema completo de carga de datos desde CSV a PostgreSQL
- API REST automática para consultar los datos
- Búsqueda full-text en español con PostgreSQL
- Plantillas reutilizables para cualquier tipo de catálogo

### Para Qwen
- Acceso a datos internos de la empresa mediante endpoints HTTP
- System prompts configurables para diferentes catálogos
- Respuestas basadas en datos reales, no alucinaciones
- Búsqueda inteligente con stemming en español

## Catálogos Implementados

### 1. CIE-10 (Códigos Médicos)
- **Registros**: 14,498 códigos de enfermedades
- **Endpoints**:
  - `GET /cie10/search?q=diabetes` - Búsqueda
  - `GET /cie10/E10` - Código específico
  - `GET /cie10/` - Estadísticas
- **Uso**: Codificación de diagnósticos médicos
- **Documentación**: [CIE10_IMPLEMENTATION.md](CIE10_IMPLEMENTATION.md)

### 2. Plantilla Genérica
- **Archivo**: [CSV_LOADING_GUIDE.md](CSV_LOADING_GUIDE.md)
- **Casos de uso**:
  - Catálogos de productos/servicios
  - Listas de empleados/departamentos
  - Inventarios y materiales
  - Códigos de procedimientos
  - Cualquier dato estructurado

## Inicio Rápido

### Para Usuarios Finales

1. **Seleccionar el prompt adecuado** en el chat:
   - "Asistente Médico CIE-10" para códigos médicos
   - Otros prompts según el catálogo que necesites

2. **Hacer preguntas naturales**:
   ```
   Usuario: ¿Qué código CIE-10 es diabetes tipo 1?
   Qwen: El código es E10 - Diabetes mellitus insulinodependiente
   ```

### Para Desarrolladores

1. **Preparar tu CSV**:
   ```csv
   code,name,description,category
   ITEM001,Item A,Descripción del item,Categoria 1
   ITEM002,Item B,Descripción del item,Categoria 2
   ```

2. **Seguir la guía**:
   - Leer [CSV_LOADING_GUIDE.md](CSV_LOADING_GUIDE.md)
   - Crear modelo en `src/models.py`
   - Crear router en `src/routes/`
   - Crear script de carga en `scripts/`
   - Cargar datos y probar

3. **Tiempo estimado**: 30-60 minutos para un catálogo nuevo

## Arquitectura Técnica

### Stack
- **Backend**: FastAPI + SQLAlchemy
- **Base de datos**: PostgreSQL 14+
- **Búsqueda**: PostgreSQL Full-Text Search (GIN index)
- **LLM**: Qwen 2.5 vía Ollama

### Flujo de Datos

```
CSV File → Python Script → PostgreSQL → FastAPI → Qwen
                ↓              ↓          ↓         ↓
         load_script.py   to_tsvector  /api   system_prompt
```

### Componentes

```
energyapp-llm-platform/
├── docs/
│   ├── CIE10_IMPLEMENTATION.md       # Implementación CIE-10
│   ├── CSV_LOADING_GUIDE.md          # Guía genérica
│   └── README_CSV_FEATURES.md        # Este archivo
├── scripts/
│   └── load_cie10.py                 # Script de carga CIE-10
├── src/
│   ├── models.py                     # CIE10Code model
│   ├── schemas.py                    # CIE10CodeResponse schema
│   └── routes/
│       └── cie10.py                  # API endpoints
└── cie-10.csv                        # Datos fuente
```

## Características Clave

### 1. Búsqueda Inteligente
- Full-text search en español
- Stemming automático ("diabético" → "diabetes")
- Búsqueda por código o descripción
- Ordenamiento por relevancia

### 2. Performance
- Índices GIN para búsquedas rápidas (~5-10ms)
- Carga eficiente de datos (commits por lotes)
- Caché a nivel de PostgreSQL

### 3. Facilidad de Uso
- Scripts automatizados de carga
- API REST estándar
- Documentación completa
- Ejemplos de uso

### 4. Integración con Qwen
- System prompts configurables
- Ejemplos de conversaciones
- Formato de respuestas estructurado
- Sin alucinaciones (datos reales)

## Configurar Qwen para un Catálogo

### Método 1: System Prompt en Base de Datos

```sql
INSERT INTO system_prompts (name, content, is_active, created_by)
VALUES (
  'Mi Catálogo',
  'Eres un asistente con acceso a <descripción del catálogo>.

   Usa estos endpoints:
   - GET http://localhost:8001/<ruta>/search?q=<término>
   - GET http://localhost:8001/<ruta>/<código>

   Siempre busca en el catálogo antes de responder.',
  true,
  1
);
```

### Método 2: Modelfile en Ollama

```dockerfile
FROM qwen2.5:7b

SYSTEM """
Eres un asistente con acceso a datos internos.
Endpoint: GET http://localhost:8001/<ruta>/search
"""

PARAMETER temperature 0.2
```

```bash
ollama create qwen-catalogo -f Modelfile
```

## Casos de Uso Reales

### 1. Soporte Médico
**Catálogo**: CIE-10
**Uso**: Codificación de diagnósticos para facturación
**Pregunta**: "¿Cuál es el código para hipertensión arterial?"
**Respuesta**: Código I10 con explicación

### 2. Catálogo de Productos
**Catálogo**: Productos internos
**Uso**: Consulta de SKUs y precios
**Pregunta**: "¿Cuánto cuesta el producto XYZ?"
**Respuesta**: Precio y descripción del producto

### 3. Base de Conocimiento Interna
**Catálogo**: Procedimientos/políticas
**Uso**: Onboarding y capacitación
**Pregunta**: "¿Cuál es el procedimiento para X?"
**Respuesta**: Paso a paso con código de referencia

### 4. Inventario
**Catálogo**: Stock de materiales
**Uso**: Verificación de disponibilidad
**Pregunta**: "¿Tenemos material ABC?"
**Respuesta**: Cantidad y ubicación

## Ventajas vs Otras Soluciones

### vs RAG (Retrieval-Augmented Generation)
- ✅ Más rápido (consulta directa vs embeddings)
- ✅ Datos estructurados (códigos exactos)
- ✅ Más simple de implementar
- ❌ Menos flexible para texto libre

### vs Fine-tuning
- ✅ Sin necesidad de re-entrenar modelos
- ✅ Datos actualizables en tiempo real
- ✅ Menor costo computacional
- ❌ Depende de conectividad

### vs Prompts con Datos Embebidos
- ✅ No limita el contexto del modelo
- ✅ Escalable a miles de registros
- ✅ Búsqueda optimizada
- ❌ Requiere infraestructura de backend

## Mantenimiento

### Actualizar Datos
```bash
# 1. Reemplazar CSV
scp nuevo-catalogo.csv root@servidor:/root/energyapp-llm-platform/

# 2. Limpiar tabla
ssh root@servidor "psql -U energyapp -d energyapp -c 'TRUNCATE TABLE mi_tabla;'"

# 3. Recargar
ssh root@servidor "cd /root/energyapp-llm-platform && python3 scripts/load_script.py"
```

### Backup
```bash
# Exportar datos
pg_dump -U energyapp -t mi_tabla energyapp > backup.sql

# Importar datos
psql -U energyapp energyapp < backup.sql
```

### Monitoreo
```bash
# Estadísticas de uso
curl http://localhost:8001/mi-catalogo/

# Verificar índices
psql -U energyapp -d energyapp -c "\d+ mi_tabla"

# Performance de búsquedas
psql -U energyapp -d energyapp -c "EXPLAIN ANALYZE SELECT * FROM mi_tabla WHERE search_vector @@ plainto_tsquery('spanish', 'término');"
```

## Próximos Pasos

### Mejoras Planificadas

1. **Autocompletar**: Endpoint para sugerencias mientras se escribe
2. **Caché**: Redis para búsquedas frecuentes
3. **Sinónimos**: Tabla de términos alternativos
4. **Jerarquía navegable**: Explorar relaciones padre-hijo
5. **Exportación**: Generar reportes en CSV/Excel
6. **Versionado**: Historial de cambios en catálogos

### Nuevos Catálogos Sugeridos

- ✅ CIE-10 (implementado)
- ⏳ Catálogo de procedimientos médicos
- ⏳ Códigos de medicamentos
- ⏳ Catálogo de servicios de la empresa
- ⏳ Base de conocimiento interna
- ⏳ Directorio de empleados
- ⏳ Inventario de equipos

## Soporte

### Problemas Comunes

Ver sección "Troubleshooting" en:
- [CSV_LOADING_GUIDE.md](CSV_LOADING_GUIDE.md#troubleshooting)

### Contacto

Para preguntas sobre:
- **Implementación técnica**: Revisar guías en `/docs`
- **Nuevos catálogos**: Seguir plantilla en `CSV_LOADING_GUIDE.md`
- **Problemas de producción**: Revisar logs en `/var/log/fastapi.log`

## Referencias

- [Documentación PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Qwen Model](https://qwenlm.github.io/)

---

**Última actualización**: Diciembre 2024
**Versión**: 1.0
**Autor**: EnergyApp LLM Platform Team
