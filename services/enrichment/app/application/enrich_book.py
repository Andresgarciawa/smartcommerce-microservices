import uuid
import datetime
import logging
import sys
import os

# Añadir el root directory para poder importar shared.config_client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.domain.models import EnrichmentRequest, EnrichmentResult
from app.infraestructure.orm_models import EnrichmentRequestORM, EnrichmentResultORM
from app.infraestructure.external_apis import (
    fetch_from_google_books,
    fetch_from_open_library,
    fetch_from_crossref,
    enrich_with_retries
)
from sqlalchemy.orm import Session

try:
    from shared.config_client import get_client
except ImportError:
    get_client = None

logger = logging.getLogger(__name__)

async def run(request: EnrichmentRequest, db: Session = None) -> EnrichmentResult:
    """
    Caso de uso: Enriquecer datos de un libro llamando a APIs externas
    y usando configuración desde Config Service.
    """
    request_id = str(uuid.uuid4())
    
    # Valores por defecto
    priority_sources = ["GOOGLE_BOOKS", "CROSSREF", "OPEN_LIBRARY"]
    retries = 3
    timeout = 5
    
    # Obtener configuración desde Config Service (Dev8)
    if get_client:
        try:
            config_client = get_client()
            priority_sources = config_client.get("enrichment.priority_sources", default=priority_sources)
            retries = config_client.get("enrichment.retry_attempts", default=retries)
            timeout_ms = config_client.get("enrichment.timeout_ms", default=5000)
            timeout = int(timeout_ms / 1000)
        except Exception as e:
            logger.warning(f"No se pudo cargar la configuración del servicio: {e}")

    result_data = None
    
    api_map = {
        "GOOGLE_BOOKS": fetch_from_google_books,
        "OPEN_LIBRARY": fetch_from_open_library,
        "CROSSREF": fetch_from_crossref
    }
    
    for source in priority_sources:
        fetch_func = api_map.get(source)
        if not fetch_func:
            continue
            
        logger.info(f"Intentando enriquecer {request.book_reference} usando {source}...")
        data = await enrich_with_retries(fetch_func, request.book_reference, retries=retries, timeout=timeout)
        if data:
            result_data = data
            break
            
    if not result_data:
        # Fallback si todas las APIs fallan
        result_data = {
            "source": "FALLBACK",
            "title": f"[Enriched] {request.book_reference}",
            "author": "Desconocido",
            "publisher": "Desconocido",
            "description": "No se encontraron datos en las APIs externas.",
            "cover_url": None
        }

    result_domain = EnrichmentResult(
        id=str(uuid.uuid4()),
        request_id=request_id,
        normalized_title=result_data.get("title") or request.book_reference,
        normalized_author=result_data.get("author") or "Desconocido",
        normalized_publisher=result_data.get("publisher") or "Desconocido",
        normalized_description=result_data.get("description"),
        cover_url=result_data.get("cover_url"),
        metadata_json={
            "source": result_data.get("source"),
            "enriched_at": datetime.datetime.utcnow().isoformat(),
            "book_reference": request.book_reference
        }
    )

    # Persistencia en base de datos
    if db:
        try:
            req_orm = EnrichmentRequestORM(
                id=request_id,
                book_reference=request.book_reference,
                source_used=result_data.get("source"),
                status="completed" if result_data.get("source") != "FALLBACK" else "failed"
            )
            db.add(req_orm)
            
            res_orm = EnrichmentResultORM(
                id=result_domain.id,
                request_id=request_id,
                normalized_title=result_domain.normalized_title,
                normalized_author=result_domain.normalized_author,
                normalized_publisher=result_domain.normalized_publisher,
                normalized_description=result_domain.normalized_description,
                cover_url=result_domain.cover_url,
                metadata_json=result_domain.metadata_json
            )
            db.add(res_orm)
            
            db.commit()
            logger.info(f"Enriquecimiento guardado en BD para {request.book_reference}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error guardando en BD: {e}")

    return result_domain
