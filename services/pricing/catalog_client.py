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


@dataclass
class CatalogUpdateResult:
    synced: bool
    reachable: bool
    payload: dict[str, Any] | None = None
    error_message: str | None = None


class CatalogClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_book(self, book_id: str) -> CatalogBookLookup:
        endpoint = f"{self.base_url}/api/catalog/books/{book_id}"
        http_request = request.Request(endpoint, method="GET")

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return CatalogBookLookup(exists=True, reachable=True, payload=payload)
        except error.HTTPError as http_error:
            if http_error.code == 404:
                return CatalogBookLookup(
                    exists=False,
                    reachable=True,
                    error_message="El libro solicitado no existe en Catalog Service.",
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

    def update_book_price(
        self,
        book_id: str,
        suggested_price: float,
        currency: str,
        price_source: str,
    ) -> CatalogUpdateResult:
        endpoint = f"{self.base_url}/api/catalog/books/{book_id}"
        payload = json.dumps(
            {
                "suggested_price": suggested_price,
                "currency": currency,
                "price_source": price_source,
            }
        ).encode("utf-8")
        http_request = request.Request(
            endpoint,
            data=payload,
            method="PUT",
            headers={"Content-Type": "application/json"},
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
                return CatalogUpdateResult(synced=True, reachable=True, payload=body)
        except error.HTTPError as http_error:
            return CatalogUpdateResult(
                synced=False,
                reachable=http_error.code < 500,
                error_message=f"Catalog Service respondio con HTTP {http_error.code}.",
            )
        except (error.URLError, TimeoutError) as connection_error:
            return CatalogUpdateResult(
                synced=False,
                reachable=False,
                error_message=f"No se pudo sincronizar Catalog Service: {connection_error}.",
            )
