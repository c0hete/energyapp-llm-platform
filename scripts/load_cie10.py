"""
Script para cargar códigos CIE-10 desde CSV a PostgreSQL
Uso: python scripts/load_cie10.py
"""
import csv
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import SessionLocal
from src.models import CIE10Code
from sqlalchemy import text

def load_cie10_from_csv(csv_path: str):
    """Carga códigos CIE-10 desde CSV a la base de datos"""
    db = SessionLocal()

    try:
        print(f"Leyendo CSV desde: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Total de filas en CSV: {len(rows)}")

        # Procesar cada fila
        added = 0
        skipped = 0

        for row in rows:
            code = row['code'].strip()
            description = row['description'].strip()
            level = int(row['level'])

            # Determinar si es un rango (contiene guión)
            is_range = '-' in code

            # Determinar el código padre desde las columnas code_0 a code_4
            parent_code = None
            for i in range(4, -1, -1):  # Revisar de code_4 a code_0
                col_name = f'code_{i}'
                if row.get(col_name) and row[col_name].strip() and row[col_name].strip() != code:
                    parent_code = row[col_name].strip()
                    break

            # Verificar si ya existe
            existing = db.query(CIE10Code).filter(CIE10Code.code == code).first()
            if existing:
                skipped += 1
                continue

            # Crear nuevo código
            cie_code = CIE10Code(
                code=code,
                description=description,
                level=level,
                parent_code=parent_code,
                is_range=is_range
            )
            db.add(cie_code)
            added += 1

            # Commit cada 100 registros para evitar problemas de memoria
            if added % 100 == 0:
                db.commit()
                print(f"  Procesados {added + skipped} registros...")

        # Commit final
        db.commit()

        print(f"\nCarga completada:")
        print(f"  - Agregados: {added}")
        print(f"  - Omitidos (duplicados): {skipped}")
        print(f"  - Total: {added + skipped}")

        # Actualizar el search_vector para búsqueda full-text
        print("\nActualizando índice de búsqueda full-text...")
        db.execute(text("""
            UPDATE cie10_codes
            SET search_vector = to_tsvector('spanish', code || ' ' || description)
            WHERE search_vector IS NULL
        """))
        db.commit()
        print("Índice actualizado correctamente")

        # Mostrar estadísticas
        total = db.query(CIE10Code).count()
        ranges = db.query(CIE10Code).filter(CIE10Code.is_range == True).count()
        specific = db.query(CIE10Code).filter(CIE10Code.is_range == False).count()

        print(f"\nEstadísticas finales:")
        print(f"  - Total de códigos: {total}")
        print(f"  - Rangos/categorías: {ranges}")
        print(f"  - Códigos específicos: {specific}")

    except Exception as e:
        print(f"Error durante la carga: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    csv_file = Path(__file__).parent.parent / "cie-10.csv"

    if not csv_file.exists():
        print(f"Error: No se encontró el archivo {csv_file}")
        sys.exit(1)

    print("=" * 60)
    print("CARGA DE CÓDIGOS CIE-10")
    print("=" * 60)

    load_cie10_from_csv(str(csv_file))

    print("\n" + "=" * 60)
    print("CARGA COMPLETADA")
    print("=" * 60)
