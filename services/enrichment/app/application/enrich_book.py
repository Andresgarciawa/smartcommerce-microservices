import uuid
import datetime
from app.domain.models import EnrichmentRequest, EnrichmentResult


def run(request: EnrichmentRequest) -> EnrichmentResult:
    """
    Caso de uso: Enriquecer datos de un libro.
    Sprint 1 — Mock: devuelve datos simulados sin llamar a APIs externas.
    """
    request_id = str(uuid.uuid4())

    return EnrichmentResult(
        id=str(uuid.uuid4()),
        request_id=request_id,
        normalized_title=f"[Enriched] {request.book_reference}",
        normalized_author="Autor Estandarizado (Mock)",
        normalized_publisher="Editorial Global (Mock)",
        normalized_description="Descripción enriquecida automáticamente. Pendiente integración con API real.",
        cover_url="https://example.com/cover-placeholder.jpg",
        metadata_json={
            "source": "mock",
            "enriched_at": datetime.datetime.utcnow().isoformat(),
            "book_reference": request.book_reference
        }
    )
