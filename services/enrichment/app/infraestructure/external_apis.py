import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


async def fetch_from_google_books(isbn: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    """Consulta la API de Google Books por ISBN."""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            if response.status_code == 429:
                logger.warning(f"Google Books rate-limit (429) para {isbn}. Saltando.")
                return None
            response.raise_for_status()
            data = response.json()
            if data.get("totalItems", 0) > 0:
                item = data["items"][0]["volumeInfo"]
                return {
                    "source": "GOOGLE_BOOKS",
                    "title": item.get("title"),
                    "author": ", ".join(item.get("authors", [])),
                    "publisher": item.get("publisher"),
                    "description": item.get("description"),
                    "cover_url": item.get("imageLinks", {}).get("thumbnail")
                }
    except httpx.TimeoutException:
        logger.warning(f"Timeout en Google Books para {isbn}")
    except Exception as e:
        logger.error(f"Error fetching from Google Books for {isbn}: {e}")
    return None


async def fetch_from_open_library(isbn: str, timeout: int = 12) -> Optional[Dict[str, Any]]:
    """Consulta la API de Open Library por ISBN."""
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            key = f"ISBN:{isbn}"
            if key in data:
                item = data[key]
                authors = [author.get("name") for author in item.get("authors", [])]
                publishers = [pub.get("name") for pub in item.get("publishers", [])]
                return {
                    "source": "OPEN_LIBRARY",
                    "title": item.get("title"),
                    "author": ", ".join(authors) if authors else None,
                    "publisher": ", ".join(publishers) if publishers else None,
                    "description": item.get("notes"),
                    "cover_url": item.get("cover", {}).get("large")
                }
            else:
                logger.warning(f"Open Library: ISBN {isbn} no encontrado en la respuesta.")
    except httpx.TimeoutException:
        logger.warning(f"Timeout en Open Library para {isbn}")
    except Exception as e:
        logger.error(f"Error fetching from Open Library for {isbn}: {e}")
    return None


async def fetch_from_crossref(isbn: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Consulta la API de Crossref por ISBN.
    Nota: Solo retorna resultado si el ISBN coincide exactamente en los datos devueltos.
    """
    url = f"https://api.crossref.org/works?query.bibliographic={isbn}&rows=1&filter=type:book"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            items = data.get("message", {}).get("items", [])
            if items:
                item = items[0]
                # Validar que el ISBN coincida
                raw_isbns = item.get("ISBN", [])
                clean_isbn = isbn.replace("-", "")
                clean_item_isbns = [i.replace("-", "") for i in raw_isbns]
                if clean_isbns := clean_item_isbns:
                    if clean_isbn not in clean_isbns:
                        logger.warning(f"Crossref devolvió un item cuyo ISBN no coincide con {isbn}. Saltando.")
                        return None
                authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get("author", [])]
                return {
                    "source": "CROSSREF",
                    "title": item.get("title", [""])[0] if item.get("title") else None,
                    "author": ", ".join(authors) if authors else None,
                    "publisher": item.get("publisher"),
                    "description": item.get("abstract"),
                    "cover_url": None
                }
    except httpx.TimeoutException:
        logger.warning(f"Timeout en Crossref para {isbn}")
    except Exception as e:
        logger.error(f"Error fetching from Crossref for {isbn}: {e}")
    return None


async def enrich_with_retries(
    fetch_func,
    isbn: str,
    retries: int = 2,
    timeout: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Ejecuta una función de fetch con reintentos.
    Si falla por rate-limit (None) en el primer intento, no reintenta más.
    """
    for attempt in range(retries):
        result = await fetch_func(isbn, timeout=timeout)
        if result:
            return result
        logger.warning(f"Intento {attempt + 1} fallido para {isbn} con {fetch_func.__name__}")
    return None
