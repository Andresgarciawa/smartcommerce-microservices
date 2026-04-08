from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class InventorySnapshot:
    reachable: bool
    items: list[dict[str, Any]]
    error_message: str | None = None


class InventoryClient:
    def __init__(self, base_url: str, timeout: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_items(self) -> InventorySnapshot:
        endpoint = f"{self.base_url}/api/inventory/items"
        http_request = request.Request(endpoint, method="GET")

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, list):
                    return InventorySnapshot(
                        reachable=False,
                        items=[],
                        error_message="Inventory Service respondio con un formato invalido.",
                    )

                return InventorySnapshot(reachable=True, items=payload)
        except (error.URLError, error.HTTPError, TimeoutError) as connection_error:
            return InventorySnapshot(
                reachable=False,
                items=[],
                error_message=f"No se pudo conectar con Inventory Service: {connection_error}.",
            )
