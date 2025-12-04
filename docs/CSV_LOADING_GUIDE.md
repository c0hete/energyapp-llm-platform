# Guía para Cargar Archivos CSV Internos

Esta guía muestra cómo cargar archivos CSV internos de la empresa en PostgreSQL para que Qwen pueda consultarlos mediante API REST. Se basa en la implementación de CIE-10.

## Casos de Uso

- Catálogos de productos/servicios internos
- Códigos médicos, diagnósticos, procedimientos
- Listas de empleados, departamentos, sucursales
- Códigos de inventario, materiales, herramientas
- Clasificaciones específicas de la industria
- Cualquier dato estructurado que Qwen necesite consultar

## Proceso General

### 1. Preparar el Archivo CSV

#### Requisitos:
- **Encoding**: UTF-8 (evita problemas con caracteres especiales)
- **Separador**: Coma `,` (estándar)
- **Primera fila**: Nombres de columnas
- **Datos limpios**: Sin filas vacías o mal formateadas

#### Verificar encoding:
```bash
file -i tu-archivo.csv
# Debe decir: charset=utf-8
```

#### Convertir a UTF-8 si es necesario:
```bash
iconv -f ISO-8859-1 -t UTF-8 archivo-original.csv > archivo-utf8.csv
```

#### Ejemplo de estructura:
```csv
code,name,description,category,status
PROD001,Producto A,Descripción del producto A,Categoria 1,active
PROD002,Producto B,Descripción del producto B,Categoria 2,active
```

### 2. Crear el Modelo en SQLAlchemy

**Archivo**: `src/models.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped
from .db import Base


class MiCatalogo(Base):
    """Descripción de tu catálogo"""
    __tablename__ = "mi_catalogo"

    # Campos obligatorios
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    code: Mapped[str] = Column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = Column(String(255), nullable=False)

    # Campos opcionales según tu CSV
    description: Mapped[str | None] = Column(Text, nullable=True)
    category: Mapped[str | None] = Column(String(100), nullable=True, index=True)
    status: Mapped[str] = Column(String(20), default="active", index=True)

    # Full-text search (recomendado para búsquedas en español)
    search_vector: Mapped[str | None] = Column(TSVECTOR, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    # Índice GIN para búsqueda full-text
    __table_args__ = (
        Index('idx_mi_catalogo_search', 'search_vector', postgresql_using='gin'),
    )
```

**Tipos de datos comunes**:
- `String(N)`: Texto corto (códigos, nombres)
- `Text`: Texto largo (descripciones)
- `Integer`: Números enteros
- `Float`: Números decimales
- `Boolean`: True/False
- `DateTime`: Fechas y horas
- `TSVECTOR`: Vector de búsqueda full-text

### 3. Crear el Schema para API

**Archivo**: `src/schemas.py`

```python
from pydantic import BaseModel


class MiCatalogoResponse(BaseModel):
    """Respuesta con datos del catálogo"""
    id: int
    code: str
    name: str
    description: str | None
    category: str | None
    status: str

    class Config:
        from_attributes = True
```

### 4. Crear el Router de API

**Archivo**: `src/routes/mi_catalogo.py`

```python
"""
Endpoints para búsqueda en mi catálogo
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List

from ..deps import get_db
from ..models import MiCatalogo
from ..schemas import MiCatalogoResponse

router = APIRouter(prefix="/mi-catalogo", tags=["mi-catalogo"])


@router.get("/search", response_model=List[MiCatalogoResponse])
async def search_catalogo(
    q: str = Query(..., min_length=2, max_length=100, description="Término de búsqueda"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de resultados"),
    category: str | None = Query(None, description="Filtrar por categoría (opcional)"),
    db: Session = Depends(get_db)
):
    """
    Buscar en el catálogo por código, nombre o descripción.

    Ejemplos:
    - `/mi-catalogo/search?q=producto` → Busca "producto" en todos los campos
    - `/mi-catalogo/search?q=PROD001` → Busca código específico
    - `/mi-catalogo/search?q=herramienta&category=Categoria1` → Busca con filtro
    """
    query = db.query(MiCatalogo)

    # Filtro por categoría (opcional)
    if category:
        query = query.filter(MiCatalogo.category == category)

    # Búsqueda full-text en español
    query = query.filter(
        or_(
            # Búsqueda por código (exacta, case-insensitive)
            func.upper(MiCatalogo.code).contains(q.upper()),
            # Búsqueda por nombre (parcial, case-insensitive)
            func.upper(MiCatalogo.name).contains(q.upper()),
            # Búsqueda full-text en descripción
            func.to_tsvector('spanish', MiCatalogo.description).op('@@')(
                func.plainto_tsquery('spanish', q)
            )
        )
    )

    # Ordenar por código
    results = query.order_by(MiCatalogo.code).limit(limit).all()

    return results


@router.get("/{code}", response_model=MiCatalogoResponse)
async def get_catalogo_item(
    code: str,
    db: Session = Depends(get_db)
):
    """
    Obtener información de un código específico.

    Ejemplo:
    - `/mi-catalogo/PROD001` → Detalles del producto PROD001
    """
    item = db.query(MiCatalogo).filter(
        func.upper(MiCatalogo.code) == code.upper()
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código '{code}' no encontrado"
        )

    return item


@router.get("/", response_model=dict)
async def get_catalogo_stats(db: Session = Depends(get_db)):
    """
    Obtener estadísticas del catálogo
    """
    total = db.query(MiCatalogo).count()
    active = db.query(MiCatalogo).filter(MiCatalogo.status == "active").count()
    categories = db.query(MiCatalogo.category).distinct().count()

    return {
        "total_items": total,
        "active_items": active,
        "total_categories": categories
    }
```

### 5. Registrar el Router

**Archivo**: `src/main.py`

```python
# Importar el router
from .routes import mi_catalogo as mi_catalogo_routes

# Registrar en la app (agregar al final, antes de incluir otros routers)
app.include_router(mi_catalogo_routes.router)
```

### 6. Crear el Script de Carga

**Archivo**: `scripts/load_mi_catalogo.py`

```python
"""
Script para cargar datos desde CSV a PostgreSQL
Uso: python scripts/load_mi_catalogo.py
"""
import csv
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import SessionLocal
from src.models import MiCatalogo
from sqlalchemy import text


def load_from_csv(csv_path: str):
    """Carga datos desde CSV a la base de datos"""
    db = SessionLocal()

    try:
        print(f"Leyendo CSV desde: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Total de filas en CSV: {len(rows)}")

        added = 0
        skipped = 0

        for row in rows:
            # Extraer campos del CSV
            code = row['code'].strip()
            name = row['name'].strip()
            description = row.get('description', '').strip() or None
            category = row.get('category', '').strip() or None
            status = row.get('status', 'active').strip()

            # Verificar si ya existe
            existing = db.query(MiCatalogo).filter(MiCatalogo.code == code).first()
            if existing:
                skipped += 1
                continue

            # Crear nuevo registro
            item = MiCatalogo(
                code=code,
                name=name,
                description=description,
                category=category,
                status=status
            )
            db.add(item)
            added += 1

            # Commit cada 100 registros
            if added % 100 == 0:
                db.commit()
                print(f"  Procesados {added + skipped} registros...")

        # Commit final
        db.commit()

        print(f"\nCarga completada:")
        print(f"  - Agregados: {added}")
        print(f"  - Omitidos (duplicados): {skipped}")

        # Actualizar vectores de búsqueda full-text
        print("\nActualizando índice de búsqueda full-text...")
        db.execute(text("""
            UPDATE mi_catalogo
            SET search_vector = to_tsvector('spanish',
                code || ' ' || name || ' ' || COALESCE(description, '')
            )
            WHERE search_vector IS NULL
        """))
        db.commit()
        print("Índice actualizado correctamente")

        # Mostrar estadísticas
        total = db.query(MiCatalogo).count()
        print(f"\nEstadísticas finales:")
        print(f"  - Total de registros: {total}")

    except Exception as e:
        print(f"Error durante la carga: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    csv_file = Path(__file__).parent.parent / "mi-catalogo.csv"

    if not csv_file.exists():
        print(f"Error: No se encontró el archivo {csv_file}")
        sys.exit(1)

    print("=" * 60)
    print("CARGA DE DATOS DESDE CSV")
    print("=" * 60)

    load_from_csv(str(csv_file))

    print("\n" + "=" * 60)
    print("CARGA COMPLETADA")
    print("=" * 60)
```

### 7. Deployment en Producción

#### Paso 1: Subir archivos al servidor
```bash
# Desde tu máquina local
scp mi-catalogo.csv root@servidor:/root/energyapp-llm-platform/
scp scripts/load_mi_catalogo.py root@servidor:/root/energyapp-llm-platform/scripts/
```

#### Paso 2: Crear tabla en producción
```bash
ssh root@servidor
cd /root/energyapp-llm-platform

# Crear tabla
python3 -c "
from src.db import engine
from src.models import Base
Base.metadata.tables['mi_catalogo'].create(engine, checkfirst=True)
"
```

#### Paso 3: Cargar datos
```bash
python3 scripts/load_mi_catalogo.py
```

#### Paso 4: Reiniciar backend
```bash
kill -9 $(pgrep -f uvicorn)
cd /root/energyapp-llm-platform
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8001 > /var/log/fastapi.log 2>&1 &
```

#### Paso 5: Verificar
```bash
# Estadísticas
curl "http://localhost:8001/mi-catalogo/"

# Búsqueda de prueba
curl "http://localhost:8001/mi-catalogo/search?q=test&limit=5"

# Código específico
curl "http://localhost:8001/mi-catalogo/PROD001"
```

## Integración con Qwen

### System Prompt para el Catálogo

```sql
INSERT INTO system_prompts (name, description, content, is_default, is_active, created_by)
VALUES (
  'Asistente de Catálogo',
  'Prompt para consultar el catálogo interno',
  'Eres un asistente que ayuda a los usuarios a encontrar información en el catálogo interno de la empresa.

IMPORTANTE: Cuando el usuario pregunte por productos, códigos o categorías, DEBES buscar en el catálogo antes de responder.

Endpoints disponibles:
- GET http://localhost:8001/mi-catalogo/search?q=<término>&limit=<número>&category=<categoría>
- GET http://localhost:8001/mi-catalogo/<código>
- GET http://localhost:8001/mi-catalogo/

Ejemplos:
- Usuario: "Busca el producto PROD001" → GET /mi-catalogo/PROD001
- Usuario: "¿Qué productos hay de herramientas?" → GET /mi-catalogo/search?q=herramientas&limit=10
- Usuario: "Muestra productos de Categoria1" → GET /mi-catalogo/search?q=&category=Categoria1

FORMATO DE RESPUESTA:
🏷️ **Código**: <código>
📦 **Nombre**: <nombre>
📝 **Descripción**: <descripción>
🗂️ **Categoría**: <categoría>
✅ **Estado**: <status>

Siempre presenta los resultados de forma clara y organizada.',
  false,
  true,
  1
);
```

### Modelfile para Ollama (Opcional)

```dockerfile
# Modelfile
FROM qwen2.5:7b

SYSTEM """
Eres un asistente de la empresa con acceso al catálogo interno.

Endpoint de búsqueda: GET http://localhost:8001/mi-catalogo/search?q=<término>

Cuando el usuario pregunte por productos o códigos, busca en el catálogo y presenta los resultados de forma clara.
"""

PARAMETER temperature 0.2
PARAMETER top_p 0.9
```

Crear: `ollama create qwen-catalogo -f Modelfile`

## Mejores Prácticas

### 1. Índices
- Siempre indexar columnas usadas en búsquedas (`code`, `category`, `status`)
- Usar índice GIN para full-text search en PostgreSQL
- No indexar columnas raramente consultadas (desperdicia espacio)

### 2. Búsqueda Full-Text
- Usar `to_tsvector('spanish', ...)` para textos en español
- Combinar búsqueda exacta (código) con búsqueda fuzzy (descripción)
- `plainto_tsquery` es más permisivo que `to_tsquery` (mejor para usuarios)

### 3. Validación de Datos
- Limpiar datos antes de insertar (`.strip()`, mayúsculas/minúsculas)
- Manejar valores nulos apropiadamente (`None` vs `""`)
- Verificar duplicados antes de insertar

### 4. Performance
- Hacer commits cada 100-1000 registros (no por cada fila)
- Crear índices DESPUÉS de cargar datos (más rápido)
- Usar `COPY` de PostgreSQL para CSVs muy grandes (>100k filas)

### 5. Mantenimiento
```bash
# Actualizar datos existentes
TRUNCATE TABLE mi_catalogo;
python3 scripts/load_mi_catalogo.py

# Backup
pg_dump -U energyapp -t mi_catalogo energyapp > backup.sql

# Restore
psql -U energyapp energyapp < backup.sql
```

## Troubleshooting

### Problema: Encoding incorrecto
```
Error: UnicodeDecodeError
```
**Solución**:
```bash
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
```

### Problema: Columna no existe
```
Error: KeyError 'column_name'
```
**Solución**: Verificar que el CSV tenga la columna en la primera fila y que coincida con el código.

### Problema: Búsqueda lenta
```sql
-- Verificar que existe el índice GIN
\d+ mi_catalogo

-- Si no existe, crear manualmente
CREATE INDEX idx_mi_catalogo_search ON mi_catalogo USING GIN(search_vector);
```

### Problema: Resultados vacíos
```python
# Verificar que search_vector tiene datos
SELECT code, search_vector FROM mi_catalogo LIMIT 5;

# Si es NULL, actualizar
UPDATE mi_catalogo
SET search_vector = to_tsvector('spanish', code || ' ' || name || ' ' || COALESCE(description, ''));
```

## Ejemplos de Catálogos

### Catálogo de Empleados
```python
class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = Column(Integer, primary_key=True)
    employee_id: Mapped[str] = Column(String(20), unique=True, index=True)
    full_name: Mapped[str] = Column(String(255), nullable=False)
    department: Mapped[str] = Column(String(100), index=True)
    position: Mapped[str] = Column(String(100))
    email: Mapped[str] = Column(String(255))
    status: Mapped[str] = Column(String(20), default="active", index=True)
```

### Catálogo de Inventario
```python
class InventoryItem(Base):
    __tablename__ = "inventory"
    id: Mapped[int] = Column(Integer, primary_key=True)
    sku: Mapped[str] = Column(String(50), unique=True, index=True)
    product_name: Mapped[str] = Column(String(255), nullable=False)
    category: Mapped[str] = Column(String(100), index=True)
    quantity: Mapped[int] = Column(Integer, default=0)
    location: Mapped[str] = Column(String(100))
    price: Mapped[float] = Column(Float)
```

### Catálogo de Procedimientos Médicos
```python
class MedicalProcedure(Base):
    __tablename__ = "medical_procedures"
    id: Mapped[int] = Column(Integer, primary_key=True)
    code: Mapped[str] = Column(String(20), unique=True, index=True)
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text)
    specialty: Mapped[str] = Column(String(100), index=True)
    duration_minutes: Mapped[int] = Column(Integer)
    cost: Mapped[float] = Column(Float)
```

## Recursos

- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [FastAPI Path Operations](https://fastapi.tiangolo.com/tutorial/path-params/)
- [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/)
