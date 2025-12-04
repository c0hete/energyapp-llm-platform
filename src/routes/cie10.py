"""
Endpoints para búsqueda de códigos CIE-10
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List

from ..deps import get_db
from ..models import CIE10Code
from ..schemas import CIE10CodeResponse

router = APIRouter(prefix="/cie10", tags=["cie10"])


@router.get("/search", response_model=List[CIE10CodeResponse])
async def search_cie10_codes(
    q: str = Query(..., min_length=2, max_length=100, description="Término de búsqueda"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de resultados"),
    db: Session = Depends(get_db)
):
    """
    Buscar códigos CIE-10 por código o descripción.

    Utiliza búsqueda full-text en español para encontrar códigos relevantes.

    Ejemplos:
    - `/cie10/search?q=diabetes` → Encuentra códigos relacionados con diabetes
    - `/cie10/search?q=E10` → Encuentra código específico E10
    - `/cie10/search?q=infarto` → Busca por término médico
    """

    # Búsqueda usando PostgreSQL full-text search
    query = db.query(CIE10Code)

    # Si el término parece un código (empieza con letra o contiene números)
    if q[0].isalpha() or any(c.isdigit() for c in q):
        # Búsqueda por código (case-insensitive) O por full-text
        query = query.filter(
            or_(
                func.upper(CIE10Code.code).contains(q.upper()),
                func.to_tsvector('spanish', CIE10Code.description).op('@@')(
                    func.plainto_tsquery('spanish', q)
                )
            )
        )
    else:
        # Solo búsqueda por descripción
        query = query.filter(
            func.to_tsvector('spanish', CIE10Code.description).op('@@')(
                func.plainto_tsquery('spanish', q)
            )
        )

    # Ordenar por relevancia: códigos específicos primero, luego por código
    results = (
        query
        .order_by(CIE10Code.is_range, CIE10Code.code)
        .limit(limit)
        .all()
    )

    return results


@router.get("/{code}", response_model=CIE10CodeResponse)
async def get_cie10_code(
    code: str,
    db: Session = Depends(get_db)
):
    """
    Obtener información de un código CIE-10 específico.

    Ejemplo:
    - `/cie10/E10` → Diabetes mellitus insulinodependiente
    """
    cie_code = db.query(CIE10Code).filter(
        func.upper(CIE10Code.code) == code.upper()
    ).first()

    if not cie_code:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código CIE-10 '{code}' no encontrado"
        )

    return cie_code


@router.get("/", response_model=dict)
async def get_cie10_stats(db: Session = Depends(get_db)):
    """
    Obtener estadísticas de la base de datos CIE-10
    """
    total = db.query(CIE10Code).count()
    ranges = db.query(CIE10Code).filter(CIE10Code.is_range == True).count()
    specific = db.query(CIE10Code).filter(CIE10Code.is_range == False).count()

    return {
        "total_codes": total,
        "ranges": ranges,
        "specific_codes": specific,
        "levels": {
            "0": db.query(CIE10Code).filter(CIE10Code.level == 0).count(),
            "1": db.query(CIE10Code).filter(CIE10Code.level == 1).count(),
            "2": db.query(CIE10Code).filter(CIE10Code.level == 2).count(),
        }
    }
