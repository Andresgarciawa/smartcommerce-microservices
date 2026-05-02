from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class EnrichmentLookup:
    found: bool
    reachable: bool
    payload: dict[str, Any] | None = None
    error_message: str | None = None


class EnrichmentClient:
    def __init__(self, base_url: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def enrich_by_isbn(self, isbn: str) -> EnrichmentLookup:
        endpoint = f"{self.base_url}/enrichment/enrich/{isbn}"
        http_request = request.Request(endpoint, method="POST")

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return EnrichmentLookup(found=True, reachable=True, payload=payload)
        except error.HTTPError as http_error:
            if http_error.code == 404:
                return EnrichmentLookup(
                    found=False,
                    reachable=True,
                    error_message="No se encontraron datos de enriquecimiento para el ISBN.",
                )
            return EnrichmentLookup(
                found=False,
                reachable=False,
                error_message=f"Enrichment Service respondio con HTTP {http_error.code}.",
            )
        except (error.URLError, TimeoutError) as connection_error:
            return EnrichmentLookup(
                found=False,
                reachable=False,
                error_message=f"No se pudo conectar con Enrichment Service: {connection_error}.",
            )
