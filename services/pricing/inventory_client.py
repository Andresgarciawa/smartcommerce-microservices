from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request


@dataclass
class InventorySnapshot:
    reachable: bool
    items: list[dict[str, Any]]
    error_message: str | None = None


class InventoryClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_items(self, book_reference: str) -> InventorySnapshot:
        query = parse.urlencode(
            {
                "book_reference": book_reference,
                "available_only": "true",
                "limit": 500,
                "offset": 0,
            }
        )
        endpoint = f"{self.base_url}/api/inventory/items?{query}"
        http_request = request.Request(endpoint, method="GET")

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return InventorySnapshot(reachable=True, items=payload)
        except error.HTTPError as http_error:
            return InventorySnapshot(
                reachable=False,
                items=[],
                error_message=f"Inventory Service respondio con HTTP {http_error.code}.",
            )
        except (error.URLError, TimeoutError) as connection_error:
            return InventorySnapshot(
                reachable=False,
                items=[],
                error_message=f"No se pudo conectar con Inventory Service: {connection_error}.",
            )
