from fastapi import APIRouter
from app.domain.models import EnrichmentRequest, EnrichmentResult
from app.application import enrich_book

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])


@router.post("/process", response_model=EnrichmentResult)
async def process_enrichment(request: EnrichmentRequest):
    """
    Recibe una solicitud de enriquecimiento y devuelve el resultado.
    Sprint 1: respuesta mock — sin llamadas a APIs externas.
    """
    return enrich_book.run(request)
