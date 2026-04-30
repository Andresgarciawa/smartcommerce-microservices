from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.domain.models import EnrichmentRequest, EnrichmentResult
from app.application import enrich_book
from app.infraestructure.database import get_db

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])


@router.post("/process", response_model=EnrichmentResult)
async def process_enrichment(
    request: EnrichmentRequest,
    book_id: str = Query(
        default=None,
        description="ID del libro en el Catalog Service. Si se provee, se notifica al Catalog al finalizar."
    ),
    db: Session = Depends(get_db)
):
    """
    Recibe una solicitud de enriquecimiento y devuelve el resultado.
    Si se provee book_id, actualiza automáticamente el libro en el Catalog Service.
    """
    return await enrich_book.run(request, db, book_id=book_id)
