from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class PricingCalculation:
    calculated: bool
    reachable: bool
    payload: dict[str, Any] | None = None
    error_message: str | None = None


class PricingClient:
    def __init__(self, base_url: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def calculate_price(self, book_reference: str) -> PricingCalculation:
        endpoint = f"{self.base_url}/api/pricing/calculate"
        payload = json.dumps({"book_reference": book_reference}).encode("utf-8")
        http_request = request.Request(
            endpoint,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
                return PricingCalculation(calculated=True, reachable=True, payload=body)
        except error.HTTPError as http_error:
            detail = http_error.read().decode("utf-8", errors="ignore")
            return PricingCalculation(
                calculated=False,
                reachable=http_error.code < 500,
                error_message=f"Pricing Service respondio con HTTP {http_error.code}. {detail}".strip(),
            )
        except (error.URLError, TimeoutError) as connection_error:
            return PricingCalculation(
                calculated=False,
                reachable=False,
                error_message=f"No se pudo conectar con Pricing Service: {connection_error}.",
            )
