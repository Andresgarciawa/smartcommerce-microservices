from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import main as gateway_main
from security import validate_token


async def _allow_request() -> None:
    return None


class GatewayRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        gateway_main.app.dependency_overrides[validate_token] = _allow_request
        self.client = TestClient(gateway_main.app)

    def tearDown(self) -> None:
        gateway_main.app.dependency_overrides.clear()

    def test_catalog_books_route_uses_real_catalog_endpoint(self) -> None:
        with patch("routes.catalog.catalog_client.get", new=AsyncMock(return_value=[{"id": "BOOK-1"}])) as mocked_get:
            response = self.client.get(
                "/catalog/books",
                params={"q": "soledad", "published": "true", "limit": 10, "offset": 5},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": "BOOK-1"}])
        mocked_get.assert_awaited_once_with(
            "/api/catalog/books",
            params={"q": "soledad", "published": True, "limit": 10, "offset": 5},
        )

    def test_inventory_items_route_uses_real_inventory_endpoint(self) -> None:
        with patch("routes.inventory.inventory_client.get", new=AsyncMock(return_value=[{"id": "INV-1"}])) as mocked_get:
            response = self.client.get(
                "/inventory/items",
                params={"book_reference": "BOOK-1", "available_only": "true"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"id": "INV-1"}])
        mocked_get.assert_awaited_once_with(
            "/api/inventory/items",
            params={"book_reference": "BOOK-1", "available_only": True, "limit": 100, "offset": 0},
        )

    def test_integration_health_reports_degraded_when_one_service_fails(self) -> None:
        async def fake_probe(name: str, client, path: str) -> dict[str, str]:
            if name == "inventory":
                return {"service": name, "status": "down", "detail": "timeout"}
            return {"service": name, "status": "up"}

        with patch("routes.integration.probe_service", new=AsyncMock(side_effect=fake_probe)):
            response = self.client.get("/integration/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(len(payload["services"]), 5)
        self.assertTrue(any(service["service"] == "inventory" and service["status"] == "down" for service in payload["services"]))


if __name__ == "__main__":
    unittest.main()
