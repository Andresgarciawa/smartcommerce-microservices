from fastapi import APIRouter, Depends, HTTPException
from app.infraestructure.orm_models import EnrichmentResultORM
from sqlalchemy.orm import Session
from app.domain.models import EnrichmentRequest, EnrichmentResult
from app.application import enrich_book
from app.infraestructure.database import get_db
import json

# Ajusta estas rutas de importación según tu estructura de carpetas real
from app.infraestructure.orm_models import EnrichmentResultORM 
from app.infraestructure.database import get_db # Verifica que la ruta sea correcta
from app.infraestructure.external_apis import (
    fetch_from_google_books, 
    fetch_from_open_library, 
    call_normalization_service
)

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])

@router.post("/process", response_model=EnrichmentResult)
async def process_enrichment(request: EnrichmentRequest, db: Session = Depends(get_db)):
    """
    Recibe una solicitud de enriquecimiento y devuelve el resultado.
    Sprint 1/2: Se integra con APIs externas según configuración Dev8 y guarda en DB.
    """
    return await enrich_book.run(request, db)

@router.post("/enrich/{isbn}")
async def enrich_book_by_isbn(isbn: str, db: Session = Depends(get_db)):
    """
    Busca un libro por ISBN, lo normaliza y guarda el resultado.
    """
    # 1. Intentar obtener datos de las APIs (flujo de cascada)
    raw_data = await fetch_from_google_books(isbn)
    if not raw_data:
        raw_data = await fetch_from_open_library(isbn)
    
    if not raw_data:
        raise HTTPException(status_code=404, detail="Book data not found in external APIs")

    # 2. Llamar al servicio de normalización
    normalized_data = await call_normalization_service(raw_data)
    
    # Si el servicio de normalización falla, usamos los datos crudos para no perder la operación
    norm = normalized_data if normalized_data else {}

    # 3. Preparar el objeto para la base de datos
    new_result = EnrichmentResultORM(
        isbn=isbn,
        source=raw_data.get("source"),
        metadata_json=raw_data, # SQLAlchemy manejará el dict como JSON
        
        normalized_title=norm.get("title") or raw_data.get("title"),
        normalized_author=norm.get("author") or raw_data.get("author"),
        normalized_publisher=norm.get("publisher") or raw_data.get("publisher"),
        normalized_year=norm.get("year") or 0,
        normalized_description=norm.get("description") or raw_data.get("description"),
        cover_url=norm.get("cover_url") or raw_data.get("cover_url")
    )

    try:
        db.add(new_result)
        db.commit()
        db.refresh(new_result)
        catalog_ready_data = {
        "isbn": new_result.isbn,
        "title": new_result.normalized_title,
        "author": new_result.normalized_author,
        "publisher": new_result.normalized_publisher,
        "year": new_result.normalized_year,
        "description": new_result.normalized_description,
        "cover_url": new_result.cover_url,
        "source_verification": new_result.source 
    }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return catalog_ready_data
    
