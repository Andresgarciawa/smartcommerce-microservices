from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.domain.models import EnrichmentRequest, EnrichmentResult
from app.application import enrich_book
from app.infraestructure.database import get_db

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])


@router.post("/process", response_model=EnrichmentResult)
async def process_enrichment(request: EnrichmentRequest, db: Session = Depends(get_db)):
    """
    Recibe una solicitud de enriquecimiento y devuelve el resultado.
    Sprint 1/2: Se integra con APIs externas según configuración Dev8 y guarda en DB.
    """
    return await enrich_book.run(request, db)
