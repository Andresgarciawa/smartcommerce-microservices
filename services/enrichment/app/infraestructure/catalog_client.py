import httpx
import logging
import os
import datetime

logger = logging.getLogger(__name__)

CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8001")


async def notify_catalog_enrichment(
    book_id: str,
    enrichment_result: dict,
    timeout: int = 10
) -> bool:
    """
    Llama al endpoint POST /api/catalog/books/{book_id}/enrich del Catalog Service
    para actualizar el libro con los datos enriquecidos.

    Schema esperado: BookEnrich
      - source (requerido): proveedor de datos (GOOGLE_BOOKS, OPEN_LIBRARY, CROSSREF)
      - title, subtitle, author, publisher, description, cover_url (opcionales)
      - suggested_price, currency, price_source (para uso de pricing service)

    Retorna True si la actualización fue exitosa, False en caso contrario.
    """
    url = f"{CATALOG_SERVICE_URL}/api/catalog/books/{book_id}/enrichment"

    payload = {
        "source": enrichment_result.get("source") or "UNKNOWN",
        "description": enrichment_result.get("normalized_description") or None,
        "cover_url": enrichment_result.get("cover_url") or None,
        "author": enrichment_result.get("normalized_author") or None,
        "publisher": enrichment_result.get("normalized_publisher") or None,
        "publication_year": enrichment_result.get("normalized_year") or None,
    }
    # Eliminar claves con valor None para no sobreescribir datos existentes
    payload = {k: v for k, v in payload.items() if v is not None}
    # source siempre es requerido
    if "source" not in payload:
        payload["source"] = "UNKNOWN"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.patch(url, json=payload)
            if response.status_code == 200:
                logger.info(f"Catalog actualizado exitosamente para book_id={book_id}")
                return True
            else:
                logger.warning(
                    f"Catalog respondió {response.status_code} para book_id={book_id}: {response.text[:200]}"
                )
                return False
    except Exception as e:
        logger.error(f"Error notificando al Catalog para book_id={book_id}: {e}")
        return False
