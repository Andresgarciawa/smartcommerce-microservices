from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class MarketReference:
    source: str
    external_price: float
    currency: str
    normalized_price: float
    title: str
    buy_link: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "external_price": float(self.external_price),
            "currency": self.currency,
            "normalized_price": float(self.normalized_price),
            "title": self.title,
            "buy_link": self.buy_link,
        }


class GoogleBooksClient:
    def __init__(
        self,
        api_key: str | None = None,
        country: str | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("GOOGLE_BOOKS_API_KEY", "")
        self.country = country if country is not None else os.getenv("GOOGLE_BOOKS_COUNTRY", "CO")
        self.timeout_seconds = timeout_seconds

    def find_references(self, book: dict[str, Any]) -> list[MarketReference]:
        return self.lookup(book)["references"]

    def lookup(self, book: dict[str, Any]) -> dict[str, Any]:
        queries = self._build_queries(book)
        lookup_result: dict[str, Any] = {
            "source": "google_books",
            "found": False,
            "reference_count": 0,
            "queries": [],
            "matched_title": None,
            "saleability": None,
            "reason": "no_query",
            "references": [],
        }

        for query, extra_params in queries:
            payload = self._request(query=query, extra_params=extra_params)
            lookup_result["queries"].append(query)
            if payload is None:
                lookup_result["reason"] = "request_failed"
                continue

            items = payload.get("items") or []
            if items:
                first_item = items[0]
                sale_info = first_item.get("saleInfo") or {}
                volume_info = first_item.get("volumeInfo") or {}
                lookup_result["found"] = True
                lookup_result["matched_title"] = lookup_result["matched_title"] or volume_info.get("title")
                lookup_result["saleability"] = lookup_result["saleability"] or sale_info.get("saleability")

            references: list[MarketReference] = []
            priced_item_saleability: str | None = None
            priced_item_title: str | None = None
            for item in items:
                reference = self._reference_from_item(item)
                if reference is None:
                    continue
                references.append(reference)
                if priced_item_title is None:
                    priced_item_title = reference.title
                    priced_item_saleability = (item.get("saleInfo") or {}).get("saleability")

            if references:
                lookup_result["reference_count"] = len(references)
                lookup_result["reason"] = "price_found"
                lookup_result["matched_title"] = priced_item_title or lookup_result["matched_title"]
                lookup_result["saleability"] = priced_item_saleability or lookup_result["saleability"]
                lookup_result["references"] = references
                return lookup_result

        if lookup_result["found"]:
            lookup_result["reason"] = "found_without_price"
        elif lookup_result["reason"] == "no_query":
            lookup_result["reason"] = "not_found"
        return lookup_result

    def _request(self, query: str, extra_params: dict[str, str]) -> dict[str, Any] | None:
        params = {
            "q": query,
            "maxResults": "5",
            "printType": "books",
            "country": self.country,
        }
        params.update(extra_params)
        if self.api_key:
            params["key"] = self.api_key

        url = f"https://www.googleapis.com/books/v1/volumes?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

    def _build_queries(self, book: dict[str, Any]) -> list[tuple[str, dict[str, str]]]:
        queries: list[tuple[str, dict[str, str]]] = []
        isbn = str(book.get("isbn", "")).strip()
        if isbn:
            queries.append((f"isbn:{isbn}", {}))

        title = str(book.get("title", "")).strip()
        author = str(book.get("author", "")).strip()
        parts: list[str] = []
        if title:
            parts.append(f"intitle:{title}")
        if author:
            parts.append(f"inauthor:{author}")
        if parts:
            queries.append((" ".join(parts), {"filter": "paid-ebooks"}))
        if title:
            queries.append((title, {"filter": "paid-ebooks"}))
        return queries

    def _reference_from_item(self, item: dict[str, Any]) -> MarketReference | None:
        sale_info = item.get("saleInfo") or {}
        price = sale_info.get("retailPrice") or sale_info.get("listPrice")
        if not isinstance(price, dict):
            return None

        amount = self._safe_float(price.get("amount"))
        currency = str(price.get("currencyCode", "")).upper().strip()
        if amount is None or amount <= 0 or not currency:
            return None

        normalized_price = self._normalize_to_cop(amount, currency)
        if normalized_price is None:
            return None

        volume_info = item.get("volumeInfo") or {}
        title = str(volume_info.get("title", "")).strip() or "Referencia Google Books"
        buy_link = sale_info.get("buyLink")
        if buy_link is not None:
            buy_link = str(buy_link)

        return MarketReference(
            source="google_books",
            external_price=amount,
            currency=currency,
            normalized_price=normalized_price,
            title=title,
            buy_link=buy_link,
        )

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_to_cop(amount: float, currency: str) -> float | None:
        conversion_to_cop = {
            "COP": 1.0,
            "USD": 4000.0,
            "EUR": 4300.0,
            "MXN": 235.0,
        }
        rate = conversion_to_cop.get(currency)
        if rate is None:
            return None
        return amount * rate
