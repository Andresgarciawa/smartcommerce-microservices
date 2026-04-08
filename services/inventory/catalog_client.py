from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class CatalogBookLookup:
    exists: bool
    reachable: bool
    payload: dict[str, Any] | None = None
    error_message: str | None = None


class CatalogClient:
    def __init__(self, base_url: str, timeout: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_book(self, book_id: str) -> CatalogBookLookup:
        endpoint = f"{self.base_url}/api/catalog/books/{book_id}"
        http_request = request.Request(endpoint, method="GET")

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return CatalogBookLookup(
                    exists=True,
                    reachable=True,
                    payload=payload,
                )
        except error.HTTPError as http_error:
            if http_error.code == 404:
                return CatalogBookLookup(
                    exists=False,
                    reachable=True,
                    error_message="El libro referenciado no existe en Catalog Service.",
                )

            return CatalogBookLookup(
                exists=False,
                reachable=False,
                error_message=f"Catalog Service respondio con HTTP {http_error.code}.",
            )
        except (error.URLError, TimeoutError) as connection_error:
            return CatalogBookLookup(
                exists=False,
                reachable=False,
                error_message=f"No se pudo conectar con Catalog Service: {connection_error}.",
            )
