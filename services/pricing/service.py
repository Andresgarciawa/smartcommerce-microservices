from __future__ import annotations

import os
import statistics
import uuid
from datetime import datetime, timezone
from typing import Any

from .catalog_client import CatalogClient
from .google_books_client import GoogleBooksClient, MarketReference
from .inventory_client import InventoryClient
from .repository import PricingRepository

CONDITION_FACTORS: dict[str, float] = {
    "new": 1.00,
    "like_new": 0.95,
    "used_good": 0.85,
    "good": 0.85,
    "used_fair": 0.70,
    "acceptable": 0.70,
    "used_poor": 0.55,
    "poor": 0.55,
    "damaged": 0.40,
    "defective": 0.30,
    "unknown": 0.75,
}

ACADEMIC_CATEGORY_HINTS = (
    "ingenier",
    "medic",
    "derecho",
    "historia",
    "ciencia",
    "filosof",
    "ensayo",
    "academ",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PricingService:
    def __init__(
        self,
        catalog_client: CatalogClient | None = None,
        inventory_client: InventoryClient | None = None,
        repository: PricingRepository | None = None,
        market_reference_client: GoogleBooksClient | None = None,
    ) -> None:
        self.catalog_client = catalog_client or CatalogClient(
            os.getenv("CATALOG_SERVICE_URL", "http://127.0.0.1:8001")
        )
        self.inventory_client = inventory_client or InventoryClient(
            os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:8000")
        )
        self.repository = repository or PricingRepository()
        self.market_reference_client = market_reference_client or GoogleBooksClient()

    def calculate_price(self, book_reference: str) -> dict[str, Any]:
        clean_reference = book_reference.strip()
        if not clean_reference:
            raise ValueError("book_reference es obligatorio.")

        book_lookup = self.catalog_client.get_book(clean_reference)
        if not book_lookup.reachable:
            raise RuntimeError(book_lookup.error_message or "Catalog Service no disponible.")
        if not book_lookup.exists or not book_lookup.payload:
            raise ValueError("El libro solicitado no existe.")

        book = book_lookup.payload
        inventory_snapshot = self.inventory_client.list_items(clean_reference)
        inventory_items = inventory_snapshot.items

        external_lookup = self._lookup_market_references(book)
        market_references = external_lookup.pop("references", [])
        base_price = self._compute_base_price(book, market_references)
        quantity_available_total = self._total_quantity_available(inventory_items)
        condition_label, condition_factor = self._compute_condition(inventory_items)
        stock_factor = self._compute_stock_factor(quantity_available_total)
        source_used = "google_books_sale_info" if market_references else "internal_rules"
        explanation = [
            f"Ajuste por condicion {condition_label}: factor {condition_factor:.2f}",
            f"Ajuste por disponibilidad total {quantity_available_total}: factor {stock_factor:.2f}",
        ]
        if market_references:
            reference_values = ", ".join(
                f"{reference.normalized_price:.0f} COP ({reference.currency})"
                for reference in market_references
            )
            explanation.insert(
                0,
                f"Precio base por referencias Google Books: {base_price:.0f} COP. Valores usados: {reference_values}",
            )
        else:
            explanation.insert(
                0,
                f"Precio base interno calculado: {base_price:.0f} COP. Google Books no entrego saleInfo usable.",
            )

        if not inventory_snapshot.reachable:
            explanation.append(
                "No fue posible consultar Inventory Service. Se aplico fallback de condicion y stock."
            )
            source_used = f"{source_used}_inventory_fallback"
        elif not inventory_items:
            explanation.append(
                "No existen items disponibles en inventario para el libro. Se aplico condicion desconocida."
            )

        raw_price = base_price * condition_factor * stock_factor
        suggested_price = self._round_price(raw_price)
        explanation.append(f"Precio sugerido final redondeado: {suggested_price:.0f} COP")

        catalog_sync = False
        update_result = self.catalog_client.update_book_price(
            clean_reference,
            suggested_price=suggested_price,
            currency="COP",
            price_source="pricing_service",
        )
        if update_result.synced:
            catalog_sync = True
            explanation.append("Catalog Service actualizado con suggested_price y price_source.")
        else:
            explanation.append(
                f"No se pudo sincronizar Catalog Service despues del calculo. {update_result.error_message}"
            )

        decision = {
            "id": str(uuid.uuid4()),
            "book_reference": clean_reference,
            "title": str(book.get("title", "")).strip() or clean_reference,
            "suggested_price": float(suggested_price),
            "currency": "COP",
            "base_price": float(base_price),
            "condition_label": condition_label,
            "condition_factor": float(round(condition_factor, 4)),
            "stock_factor": float(round(stock_factor, 4)),
            "quantity_available_total": quantity_available_total,
            "reference_count": len(market_references),
            "source_used": source_used,
            "external_lookup": external_lookup,
            "market_references": [reference.to_dict() for reference in market_references],
            "catalog_sync": catalog_sync,
            "explanation": explanation,
            "created_at": utc_now_iso(),
        }
        return self.repository.save_decision(decision)

    def calculate_prices_batch(self, book_references: list[str]) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for book_reference in book_references:
            try:
                items.append(self.calculate_price(book_reference))
            except (ValueError, RuntimeError) as error:
                errors.append(
                    {
                        "book_reference": book_reference,
                        "detail": str(error),
                    }
                )
        return {
            "items": items,
            "processed": len(items),
            "errors": errors,
        }

    def get_latest_decision(self, book_reference: str) -> dict[str, Any]:
        decision = self.repository.get_latest_decision(book_reference.strip())
        if decision is None:
            raise ValueError("No existe una decision de pricing para el libro solicitado.")
        return decision

    def list_pricing_decisions(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        safe_limit = max(1, min(limit, 200))
        safe_offset = max(0, offset)
        return self.repository.list_latest_decisions(limit=safe_limit, offset=safe_offset)

    def get_legacy_product_prices(self, book_references: list[str]) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for reference in book_references:
            try:
                decision = self.calculate_price(reference)
                items.append(
                    {
                        "product_id": decision["book_reference"],
                        "price": decision["suggested_price"],
                        "currency": decision["currency"],
                        "source_used": decision["source_used"],
                    }
                )
            except (ValueError, RuntimeError) as error:
                items.append(
                    {
                        "product_id": reference,
                        "price": None,
                        "currency": "COP",
                        "error": str(error),
                    }
                )
        return {"items": items, "message": "Pricing Service operativo"}

    def _lookup_market_references(self, book: dict[str, Any]) -> dict[str, Any]:
        try:
            if hasattr(self.market_reference_client, "lookup"):
                lookup = self.market_reference_client.lookup(book)
            else:
                references = self.market_reference_client.find_references(book)
                lookup = {
                    "source": "test_reference_client",
                    "found": bool(references),
                    "reference_count": len(references),
                    "queries": [],
                    "matched_title": None,
                    "saleability": None,
                    "reason": "price_found" if references else "not_found",
                    "references": references,
                }
        except Exception:
            return {
                "source": "google_books",
                "found": False,
                "reference_count": 0,
                "queries": [],
                "matched_title": None,
                "saleability": None,
                "reason": "request_failed",
                "references": [],
            }

        references = self._remove_outliers(lookup.get("references", []))
        lookup["references"] = references
        lookup["reference_count"] = len(references)
        return lookup

    def _compute_base_price(
        self,
        book: dict[str, Any],
        market_references: list[MarketReference] | None = None,
    ) -> float:
        if market_references:
            prices = [reference.normalized_price for reference in market_references]
            return max(statistics.median(prices), 12000.0)

        current_year = datetime.now(timezone.utc).year
        publication_year = int(book.get("publication_year") or current_year)
        age = max(0, current_year - publication_year)

        base_price = 30000.0
        if age <= 5:
            base_price += 15000.0
        elif age <= 15:
            base_price += 8000.0
        else:
            base_price += 3000.0

        category_name = str(book.get("category_name", "")).lower()
        if any(hint in category_name for hint in ACADEMIC_CATEGORY_HINTS):
            base_price += 6000.0

        if book.get("enriched_flag"):
            base_price += 4000.0
        if str(book.get("isbn", "")).strip():
            base_price += 2000.0

        return max(base_price, 12000.0)

    @staticmethod
    def _remove_outliers(references: list[MarketReference]) -> list[MarketReference]:
        if len(references) <= 2:
            return references

        prices = sorted(reference.normalized_price for reference in references)
        median = statistics.median(prices)
        lower_limit = median * 0.35
        upper_limit = median * 2.50
        return [
            reference
            for reference in references
            if lower_limit <= reference.normalized_price <= upper_limit
        ]

    def _compute_condition(self, inventory_items: list[dict[str, Any]]) -> tuple[str, float]:
        if not inventory_items:
            return "unknown", CONDITION_FACTORS["unknown"]

        weighted_total = 0.0
        quantity_total = 0
        quantities_by_condition: dict[str, int] = {}
        for item in inventory_items:
            quantity = max(0, int(item.get("quantity_available", 0)))
            condition = str(item.get("condition", "unknown")).strip().lower() or "unknown"
            factor = CONDITION_FACTORS.get(condition, CONDITION_FACTORS["unknown"])
            weighted_total += factor * quantity
            quantity_total += quantity
            quantities_by_condition[condition] = quantities_by_condition.get(condition, 0) + quantity

        if quantity_total <= 0:
            return "unknown", CONDITION_FACTORS["unknown"]

        predominant_condition = max(
            quantities_by_condition.items(),
            key=lambda entry: (entry[1], CONDITION_FACTORS.get(entry[0], 0.0)),
        )[0]
        return predominant_condition, weighted_total / quantity_total

    @staticmethod
    def _total_quantity_available(inventory_items: list[dict[str, Any]]) -> int:
        return sum(max(0, int(item.get("quantity_available", 0))) for item in inventory_items)

    @staticmethod
    def _compute_stock_factor(quantity_available_total: int) -> float:
        if quantity_available_total <= 2:
            return 1.05
        if quantity_available_total <= 5:
            return 1.00
        if quantity_available_total <= 10:
            return 0.97
        return 0.93

    @staticmethod
    def _round_price(value: float) -> float:
        rounded = round(value / 1000.0) * 1000.0
        return max(5000.0, rounded)
