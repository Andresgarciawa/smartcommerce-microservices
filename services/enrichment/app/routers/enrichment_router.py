import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application import enrich_book
from app.domain.models import CatalogReadyEnrichment, EnrichmentRequest, EnrichmentResult
from app.infraestructure.catalog_client import notify_catalog_enrichment
from app.infraestructure.database import get_db
from app.infraestructure.external_apis import (
    call_normalization_service,
    fetch_from_google_books,
    fetch_from_open_library,
)
from app.infraestructure.orm_models import EnrichmentResultORM

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])


def _build_catalog_ready_payload(result: EnrichmentResultORM) -> dict[str, object]:
    return {
        "isbn": result.isbn,
        "title": result.normalized_title,
        "author": result.normalized_author,
        "publisher": result.normalized_publisher,
        "year": result.normalized_year,
        "description": result.normalized_description,
        "cover_url": result.cover_url,
        "source_verification": result.source,
        "enrichment_id": result.id,
    }


def _get_latest_result_by_isbn(db: Session, isbn: str) -> EnrichmentResultORM | None:
    return (
        db.query(EnrichmentResultORM)
        .filter(EnrichmentResultORM.isbn == isbn)
        .order_by(EnrichmentResultORM.id.desc())
        .first()
    )


@router.post("/process", response_model=EnrichmentResult)
async def process_enrichment(
    request: EnrichmentRequest,
    book_id: str = None,
    db: Session = Depends(get_db),
):
    """
    Recibe una solicitud de enriquecimiento y devuelve el resultado.
    """
    result = await enrich_book.run(request, db)

    if book_id:
        await notify_catalog_enrichment(book_id, result.model_dump())

    return result


@router.post("/enrich/{isbn}", response_model=CatalogReadyEnrichment)
async def enrich_book_by_isbn(isbn: str, db: Session = Depends(get_db)):
    """
    Busca un libro por ISBN, lo normaliza, guarda el resultado y devuelve
    un payload listo para reutilizar en Catalog Service.
    """
    raw_data = await fetch_from_google_books(isbn)
    if not raw_data:
        raw_data = await fetch_from_open_library(isbn)

    if not raw_data:
        raise HTTPException(status_code=404, detail="Book data not found in external APIs")

    normalized_data = await call_normalization_service(raw_data)
    norm = normalized_data if normalized_data else {}

    new_result = EnrichmentResultORM(
        id=str(uuid.uuid4()),
        isbn=isbn,
        source=raw_data.get("source"),
        metadata_json=raw_data,
        normalized_title=norm.get("title") or raw_data.get("title"),
        normalized_author=norm.get("author") or raw_data.get("author"),
        normalized_publisher=norm.get("publisher") or raw_data.get("publisher"),
        normalized_year=norm.get("year")
        or (
            int(raw_data.get("published_date")[:4])
            if raw_data.get("published_date")
            and raw_data.get("published_date")[:4].isdigit()
            else 0
        ),
        normalized_description=norm.get("description") or raw_data.get("description"),
        cover_url=norm.get("cover_url") or raw_data.get("cover_url"),
    )

    try:
        db.add(new_result)
        db.commit()
        db.refresh(new_result)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(error)}")

    return _build_catalog_ready_payload(new_result)


@router.get("/isbn/{isbn}", response_model=CatalogReadyEnrichment)
async def get_enriched_book_info_by_isbn(isbn: str, db: Session = Depends(get_db)):
    """
    Consulta el ultimo enriquecimiento guardado para un ISBN.
    """
    result = _get_latest_result_by_isbn(db, isbn)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No existe informacion enriquecida para ese ISBN. Usa POST /enrichment/enrich/{isbn} primero.",
        )
    return _build_catalog_ready_payload(result)


@router.get("/result/{enrichment_id}", response_model=CatalogReadyEnrichment)
async def get_enriched_book_info_by_result_id(enrichment_id: str, db: Session = Depends(get_db)):
    """
    Consulta un resultado de enriquecimiento puntual por su id.
    """
    result = (
        db.query(EnrichmentResultORM)
        .filter(EnrichmentResultORM.id == enrichment_id)
        .first()
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No existe informacion enriquecida para ese enrichment_id.",
        )
    return _build_catalog_ready_payload(result)


@router.get("/{identifier}", response_model=CatalogReadyEnrichment)
async def get_enriched_book_info(identifier: str, db: Session = Depends(get_db)):
    """
    Consulta informacion enriquecida ya guardada.

    Busca primero por id del resultado y luego por ISBN.
    La respuesta queda lista para usar manualmente en un POST al Catalog Service.
    """
    result = (
        db.query(EnrichmentResultORM)
        .filter(EnrichmentResultORM.id == identifier)
        .first()
    )

    if result is None:
        result = _get_latest_result_by_isbn(db, identifier)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No existe informacion enriquecida para ese identificador. Usa POST /enrichment/enrich/{isbn} primero.",
        )

    return _build_catalog_ready_payload(result)
