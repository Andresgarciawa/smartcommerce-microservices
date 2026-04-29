from __future__ import annotations

import unittest
from dataclasses import dataclass

from services.pricing.google_books_client import MarketReference
from services.pricing.service import PricingService


@dataclass
class FakeCatalogLookup:
    exists: bool
    reachable: bool
    payload: dict | None = None
    error_message: str | None = None


@dataclass
class FakeCatalogUpdateResult:
    synced: bool
    reachable: bool
    payload: dict | None = None
    error_message: str | None = None


@dataclass
class FakeInventorySnapshot:
    reachable: bool
    items: list[dict]
    error_message: str | None = None


class FakeCatalogClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.updated_payloads: list[dict] = []

    def get_book(self, book_id: str) -> FakeCatalogLookup:
        return FakeCatalogLookup(exists=True, reachable=True, payload=self.payload | {"id": book_id})

    def update_book_price(self, book_id: str, suggested_price: float, currency: str, price_source: str) -> FakeCatalogUpdateResult:
        self.updated_payloads.append(
            {
                "book_id": book_id,
                "suggested_price": suggested_price,
                "currency": currency,
                "price_source": price_source,
            }
        )
        return FakeCatalogUpdateResult(synced=True, reachable=True)


class FakeInventoryClient:
    def __init__(self, items: list[dict], reachable: bool = True) -> None:
        self.items = items
        self.reachable = reachable

    def list_items(self, book_reference: str) -> FakeInventorySnapshot:
        return FakeInventorySnapshot(reachable=self.reachable, items=self.items)


class FakeMarketReferenceClient:
    def __init__(self, references: list[MarketReference] | None = None) -> None:
        self.references = references or []

    def find_references(self, book: dict) -> list[MarketReference]:
        return self.references


class InMemoryPricingRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def save_decision(self, decision: dict) -> dict:
        self.items.append(decision)
        return decision

    def get_latest_decision(self, book_reference: str) -> dict | None:
        matches = [item for item in self.items if item["book_reference"] == book_reference]
        return matches[-1] if matches else None

    def list_latest_decisions(self, limit: int, offset: int) -> dict:
        latest_by_book: dict[str, dict] = {}
        for item in self.items:
            latest_by_book[item["book_reference"]] = item
        values = list(latest_by_book.values())[offset : offset + limit]
        return {"items": values, "total": len(latest_by_book)}


class PricingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.book_payload = {
            "title": "Clean Architecture",
            "publication_year": 2021,
            "category_name": "Ingenieria",
            "enriched_flag": True,
            "isbn": "9780134494166",
        }
        self.repository = InMemoryPricingRepository()

    def test_calculate_price_generates_explanation_and_syncs_catalog(self) -> None:
        service = PricingService(
            catalog_client=FakeCatalogClient(self.book_payload),
            inventory_client=FakeInventoryClient(
                [
                    {"condition": "used_good", "quantity_available": 2},
                    {"condition": "new", "quantity_available": 1},
                ]
            ),
            repository=self.repository,
            market_reference_client=FakeMarketReferenceClient(),
        )

        result = service.calculate_price("BOOK-001")

        self.assertEqual(result["book_reference"], "BOOK-001")
        self.assertGreater(result["suggested_price"], 0)
        self.assertEqual(result["currency"], "COP")
        self.assertTrue(result["catalog_sync"])
        self.assertEqual(result["reference_count"], 0)
        self.assertGreaterEqual(len(result["explanation"]), 4)

    def test_inventory_fallback_still_calculates_price(self) -> None:
        service = PricingService(
            catalog_client=FakeCatalogClient(self.book_payload),
            inventory_client=FakeInventoryClient([], reachable=False),
            repository=self.repository,
            market_reference_client=FakeMarketReferenceClient(),
        )

        result = service.calculate_price("BOOK-002")

        self.assertEqual(result["condition_label"], "unknown")
        self.assertEqual(result["source_used"], "internal_rules_inventory_fallback")
        self.assertTrue(any("fallback" in step.lower() for step in result["explanation"]))

    def test_list_pricing_decisions_returns_latest_per_book(self) -> None:
        service = PricingService(
            catalog_client=FakeCatalogClient(self.book_payload),
            inventory_client=FakeInventoryClient([{"condition": "new", "quantity_available": 3}]),
            repository=self.repository,
            market_reference_client=FakeMarketReferenceClient(),
        )

        service.calculate_price("BOOK-003")
        service.calculate_price("BOOK-004")
        listing = service.list_pricing_decisions(limit=10, offset=0)

        self.assertEqual(listing["total"], 2)
        self.assertEqual(len(listing["items"]), 2)

    def test_google_books_reference_is_used_when_available(self) -> None:
        service = PricingService(
            catalog_client=FakeCatalogClient(self.book_payload),
            inventory_client=FakeInventoryClient([{"condition": "new", "quantity_available": 1}]),
            repository=self.repository,
            market_reference_client=FakeMarketReferenceClient(
                [
                    MarketReference(
                        source="google_books",
                        external_price=25.0,
                        currency="USD",
                        normalized_price=100000.0,
                        title="Clean Architecture",
                        buy_link="https://books.google.test/buy",
                    )
                ]
            ),
        )

        result = service.calculate_price("BOOK-005")

        self.assertEqual(result["reference_count"], 1)
        self.assertEqual(result["source_used"], "google_books_sale_info")
        self.assertEqual(result["market_references"][0]["source"], "google_books")
        self.assertTrue(any("Google Books" in step for step in result["explanation"]))


if __name__ == "__main__":
    unittest.main()
