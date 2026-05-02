from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .database import Database, build_database
from .enrichment_client import EnrichmentClient
from .inventory_client import InventoryClient
from .pricing_client import PricingClient


BOOK_SELECT = """
SELECT books.id, books.title, books.subtitle, books.author,
       books.publisher, books.publication_year, books.volume,
       books.isbn, books.issn, books.category_id,
       categories.name AS category_name, books.description,
       books.cover_url, books.summary, books.language, books.page_count,
       books.published_date, books.authors_extra, books.categories_external,
       books.thumbnail_url, books.source_provider, books.source_reference,
       books.enrichment_status, books.enrichment_score, books.last_enriched_at,
       books.suggested_price, books.currency, books.price_source, books.price_updated_at,
       books.enriched_flag, books.published_flag
FROM books
JOIN categories ON categories.id = books.category_id
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CatalogService:
    def __init__(
        self,
        sqlite_path: str | None = None,
        inventory_client: InventoryClient | None = None,
        enrichment_client: EnrichmentClient | None = None,
        pricing_client: PricingClient | None = None,
        database: Database | None = None,
    ) -> None:
        self.database = database or build_database(sqlite_path)
        self.database.initialize()
        self.placeholder = self.database.placeholder()
        self.inventory_client = inventory_client or InventoryClient(
            os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:8000")
        )
        self.enrichment_client = enrichment_client or EnrichmentClient(
            os.getenv("ENRICHMENT_SERVICE_URL", "http://127.0.0.1:8005")
        )
        self.pricing_client = pricing_client or PricingClient(
            os.getenv("PRICING_SERVICE_URL", "http://127.0.0.1:8003")
        )

    def create_category(self, name: str, description: str = "") -> dict[str, Any]:
        clean_name = name.strip()
        clean_description = description.strip()
        if not clean_name:
            raise ValueError("name es obligatorio.")

        category = {
            "id": str(uuid.uuid4()),
            "name": clean_name,
            "description": clean_description,
            "created_at": utc_now_iso(),
        }
        query = f"""
        INSERT INTO categories (id, name, description, created_at)
        VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
        """
        try:
            with self.database.connection() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    query,
                    (
                        category["id"],
                        category["name"],
                        category["description"],
                        category["created_at"],
                    ),
                )
                connection.commit()
        except Exception as error:
            if "unique" in str(error).lower():
                raise ValueError("Ya existe una categoria con ese nombre.") from error
            raise
        return self.get_category(category["id"])

    def list_categories(self) -> list[dict[str, Any]]:
        query = "SELECT id, name, description, created_at FROM categories ORDER BY name ASC"
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [self.database.row_factory(cursor, row) for row in rows]

    def get_category(self, category_id: str) -> dict[str, Any]:
        query = f"""
        SELECT id, name, description, created_at
        FROM categories
        WHERE id = {self.placeholder}
        """
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, (category_id,))
            row = cursor.fetchone()
            if row is None:
                raise ValueError("La categoria solicitada no existe.")
            return self.database.row_factory(cursor, row)

    def create_book(self, payload: dict[str, Any]) -> dict[str, Any]:
        book = self._validate_book_payload(payload)
        query = f"""
        INSERT INTO books (
            id, title, subtitle, author, publisher, publication_year,
            volume, isbn, issn, category_id, description, cover_url,
            summary, language, page_count, published_date, authors_extra,
            categories_external, thumbnail_url, source_provider,
            source_reference, enrichment_status, enrichment_score,
            last_enriched_at, suggested_price, currency, price_source,
            price_updated_at, enriched_flag, published_flag, created_at, updated_at
        ) VALUES (
            {", ".join([self.placeholder] * 32)}
        )
        """
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                (
                    book["id"],
                    book["title"],
                    book["subtitle"],
                    book["author"],
                    book["publisher"],
                    book["publication_year"],
                    book["volume"],
                    book["isbn"],
                    book["issn"],
                    book["category_id"],
                    book["description"],
                    book["cover_url"],
                    book["summary"],
                    book["language"],
                    book["page_count"],
                    book["published_date"],
                    book["authors_extra"],
                    book["categories_external"],
                    book["thumbnail_url"],
                    book["source_provider"],
                    book["source_reference"],
                    book["enrichment_status"],
                    book["enrichment_score"],
                    book["last_enriched_at"],
                    book["suggested_price"],
                    book["currency"],
                    book["price_source"],
                    book["price_updated_at"],
                    self.database.bool_value(book["enriched_flag"]),
                    self.database.bool_value(book["published_flag"]),
                    book["created_at"],
                    book["updated_at"],
                ),
            )
            connection.commit()
        return self.get_book(book["id"])

    def list_books(
        self,
        *,
        q: str | None = None,
        category_id: str | None = None,
        enriched_only: bool | None = None,
        published_only: bool | None = None,
    ) -> list[dict[str, Any]]:
        query = [BOOK_SELECT]
        params: list[Any] = []
        filters: list[str] = []

        if q:
            lookup = f"%{q.strip().lower()}%"
            filters.append(
                f"""(
                    LOWER(books.title) LIKE {self.placeholder}
                    OR LOWER(books.author) LIKE {self.placeholder}
                    OR LOWER(books.isbn) LIKE {self.placeholder}
                )"""
            )
            params.extend([lookup, lookup, lookup])
        if category_id:
            filters.append(f"books.category_id = {self.placeholder}")
            params.append(category_id)
        if enriched_only is not None:
            filters.append(f"books.enriched_flag = {self.placeholder}")
            params.append(self.database.bool_value(enriched_only))
        if published_only is not None:
            filters.append(f"books.published_flag = {self.placeholder}")
            params.append(self.database.bool_value(published_only))

        if filters:
            query.append("WHERE " + " AND ".join(filters))
        query.append("ORDER BY books.updated_at DESC, books.title ASC")

        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute("\n".join(query), tuple(params))
            rows = cursor.fetchall()
            result = [self._deserialize_book_row(self.database.row_factory(cursor, row)) for row in rows]

        inventory_snapshot = self.inventory_client.list_items()
        inventory_index = self._build_inventory_index(inventory_snapshot.items)
        return [
            self._map_book_row(
                row,
                inventory_stats=inventory_index.get(row["id"]),
                inventory_sync=inventory_snapshot.reachable,
            )
            for row in result
        ]

    def get_book(self, book_id: str) -> dict[str, Any]:
        query = BOOK_SELECT + f"\nWHERE books.id = {self.placeholder}"
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, (book_id,))
            row = cursor.fetchone()
            if row is None:
                raise ValueError("El libro solicitado no existe.")
            result = self._deserialize_book_row(self.database.row_factory(cursor, row))

        inventory_snapshot = self.inventory_client.list_items()
        inventory_index = self._build_inventory_index(inventory_snapshot.items)
        return self._map_book_row(
            result,
            inventory_stats=inventory_index.get(result["id"]),
            inventory_sync=inventory_snapshot.reachable,
        )

    def apply_enrichment(self, book_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.get_book(book_id)
        merged = self._merge_enrichment(current, payload)
        query = f"""
        UPDATE books
        SET title = {self.placeholder},
            author = {self.placeholder},
            publisher = {self.placeholder},
            description = {self.placeholder},
            cover_url = {self.placeholder},
            summary = {self.placeholder},
            language = {self.placeholder},
            page_count = {self.placeholder},
            published_date = {self.placeholder},
            authors_extra = {self.placeholder},
            categories_external = {self.placeholder},
            thumbnail_url = {self.placeholder},
            source_provider = {self.placeholder},
            source_reference = {self.placeholder},
            enrichment_status = {self.placeholder},
            enrichment_score = {self.placeholder},
            last_enriched_at = {self.placeholder},
            enriched_flag = {self.placeholder},
            publication_year = {self.placeholder},
            updated_at = {self.placeholder}
        WHERE id = {self.placeholder}
        """
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                (
                    merged["title"],
                    merged["author"],
                    merged["publisher"],
                    merged["description"],
                    merged["cover_url"],
                    merged["summary"],
                    merged["language"],
                    merged["page_count"],
                    merged["published_date"],
                    json.dumps(merged["authors_extra"], ensure_ascii=True),
                    json.dumps(merged["categories_external"], ensure_ascii=True),
                    merged["thumbnail_url"],
                    merged["source_provider"],
                    merged["source_reference"],
                    merged["enrichment_status"],
                    merged["enrichment_score"],
                    merged["last_enriched_at"],
                    self.database.bool_value(merged["enriched_flag"]),
                    merged["publication_year"],
                    merged["updated_at"],
                    book_id,
                ),
            )
            connection.commit()
        return self.get_book(book_id)

    def update_book(self, book_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.get_book(book_id)
        suggested_price = current.get("suggested_price")
        if "suggested_price" in payload and payload["suggested_price"] is not None:
            try:
                suggested_price = float(payload["suggested_price"])
            except (TypeError, ValueError) as error:
                raise ValueError("suggested_price debe ser numerico.") from error

        currency = str(payload.get("currency", current.get("currency") or "COP")).strip() or "COP"
        price_source = str(payload.get("price_source", current.get("price_source") or "")).strip()
        price_updated_at = str(
            payload.get("price_updated_at")
            or current.get("price_updated_at")
            or utc_now_iso()
        ).strip()
        published_flag = bool(payload.get("published_flag", current.get("published_flag", False)))

        query = f"""
        UPDATE books
        SET suggested_price = {self.placeholder},
            currency = {self.placeholder},
            price_source = {self.placeholder},
            price_updated_at = {self.placeholder},
            published_flag = {self.placeholder},
            updated_at = {self.placeholder}
        WHERE id = {self.placeholder}
        """
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                (
                    suggested_price,
                    currency,
                    price_source,
                    price_updated_at,
                    self.database.bool_value(published_flag),
                    utc_now_iso(),
                    book_id,
                ),
            )
            connection.commit()
        return self.get_book(book_id)

    def integrate_book(self, book_id: str) -> dict[str, Any]:
        book = self.get_book(book_id)
        steps: list[dict[str, str]] = []

        isbn = str(book.get("isbn", "")).strip()
        if isbn:
            enrichment_result = self.enrichment_client.enrich_by_isbn(isbn)
            if enrichment_result.reachable and enrichment_result.found and enrichment_result.payload:
                payload = {
                    "title": enrichment_result.payload.get("title", ""),
                    "author": enrichment_result.payload.get("author", ""),
                    "publisher": enrichment_result.payload.get("publisher", ""),
                    "description": enrichment_result.payload.get("description", ""),
                    "cover_url": enrichment_result.payload.get("cover_url", ""),
                    "published_date": enrichment_result.payload.get("published_date", ""),
                    "source_provider": enrichment_result.payload.get("source_verification", ""),
                    "source_reference": isbn,
                    "enrichment_status": "completed",
                    "enriched_flag": True,
                }
                year = enrichment_result.payload.get("year")
                if year:
                    payload["publication_year"] = year
                book = self.apply_enrichment(book_id, payload)
                steps.append(
                    {
                        "step": "enrichment",
                        "status": "completed",
                        "detail": "Catalogo enriquecido desde Enrichment Service.",
                    }
                )
            else:
                steps.append(
                    {
                        "step": "enrichment",
                        "status": "skipped" if enrichment_result.reachable else "degraded",
                        "detail": enrichment_result.error_message or "No se aplico enriquecimiento.",
                    }
                )
        else:
            steps.append(
                {
                    "step": "enrichment",
                    "status": "skipped",
                    "detail": "El libro no tiene ISBN para consultar Enrichment Service.",
                }
            )

        pricing_result = self.pricing_client.calculate_price(book_id)
        if pricing_result.reachable and pricing_result.calculated:
            book = self.get_book(book_id)
            steps.append(
                {
                    "step": "pricing",
                    "status": "completed",
                    "detail": "Precio sugerido calculado por Pricing Service y sincronizado en Catalog.",
                }
            )
        else:
            steps.append(
                {
                    "step": "pricing",
                    "status": "degraded",
                    "detail": pricing_result.error_message or "No se pudo calcular el precio sugerido.",
                }
            )

        return {"book": book, "steps": steps}

    def get_summary(self) -> dict[str, int]:
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT COUNT(*),
                       COALESCE(SUM(CASE WHEN published_flag THEN 1 ELSE 0 END), 0),
                       COALESCE(SUM(CASE WHEN enriched_flag THEN 1 ELSE 0 END), 0)
                FROM books
                """
            )
            row = cursor.fetchone()
        return {
            "total_categories": total_categories,
            "total_books": row[0],
            "published_books": row[1],
            "enriched_books": row[2],
        }

    def delete_category(self, category_id: str) -> None:
        self.get_category(category_id)
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT COUNT(*) FROM books WHERE category_id = {self.placeholder}",
                (category_id,),
            )
            count = cursor.fetchone()[0]
            if count > 0:
                raise ValueError("No se puede eliminar la categoria porque tiene libros asociados.")
            cursor.execute(
                f"DELETE FROM categories WHERE id = {self.placeholder}",
                (category_id,),
            )
            connection.commit()

    def delete_book(self, book_id: str) -> None:
        self.get_book(book_id)
        inventory_snapshot = self.inventory_client.list_items()
        linked = [
            item for item in inventory_snapshot.items if str(item.get("book_reference", "")).strip() == book_id
        ]
        if inventory_snapshot.reachable and linked:
            raise ValueError("No se puede eliminar el libro porque tiene inventario asociado.")
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"DELETE FROM books WHERE id = {self.placeholder}", (book_id,))
            connection.commit()

    def _validate_book_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = str(payload.get("title", "")).strip()
        author = str(payload.get("author", "")).strip()
        publisher = str(payload.get("publisher", "")).strip()
        isbn = str(payload.get("isbn", "")).strip()
        issn = str(payload.get("issn", "")).strip()
        category_id = str(payload.get("category_id", "")).strip()
        if not title:
            raise ValueError("title es obligatorio.")
        if not author:
            raise ValueError("author es obligatorio.")
        if not publisher:
            raise ValueError("publisher es obligatorio.")
        if not isbn and not issn:
            raise ValueError("Debes enviar al menos uno de estos identificadores: isbn o issn.")
        if not category_id:
            raise ValueError("category_id es obligatorio.")
        self.get_category(category_id)

        try:
            publication_year = int(payload.get("publication_year", 0))
        except (TypeError, ValueError) as error:
            raise ValueError("publication_year debe ser numerico.") from error

        current_year = datetime.now(timezone.utc).year
        if publication_year < 1000 or publication_year > current_year:
            raise ValueError("publication_year esta fuera de rango.")

        timestamp = utc_now_iso()
        return {
            "id": str(uuid.uuid4()),
            "title": title,
            "subtitle": str(payload.get("subtitle", "")).strip(),
            "author": author,
            "publisher": publisher,
            "publication_year": publication_year,
            "volume": str(payload.get("volume", "")).strip(),
            "isbn": isbn,
            "issn": issn,
            "category_id": category_id,
            "description": str(payload.get("description", "")).strip(),
            "cover_url": str(payload.get("cover_url", "")).strip(),
            "summary": str(payload.get("summary", "")).strip(),
            "language": str(payload.get("language", "")).strip(),
            "page_count": max(int(payload.get("page_count", 0) or 0), 0),
            "published_date": str(payload.get("published_date", "")).strip(),
            "authors_extra": json.dumps(payload.get("authors_extra", []), ensure_ascii=True),
            "categories_external": json.dumps(payload.get("categories_external", []), ensure_ascii=True),
            "thumbnail_url": str(payload.get("thumbnail_url", "")).strip(),
            "source_provider": str(payload.get("source_provider", "")).strip(),
            "source_reference": str(payload.get("source_reference", "")).strip(),
            "enrichment_status": str(payload.get("enrichment_status", "pending")).strip() or "pending",
            "enrichment_score": float(payload.get("enrichment_score", 0) or 0),
            "last_enriched_at": str(payload.get("last_enriched_at", "")).strip(),
            "suggested_price": (
                float(payload.get("suggested_price", 0) or 0)
                if payload.get("suggested_price") not in (None, "")
                else None
            ),
            "currency": str(payload.get("currency", "COP")).strip() or "COP",
            "price_source": str(payload.get("price_source", "")).strip(),
            "price_updated_at": str(payload.get("price_updated_at", "")).strip(),
            "enriched_flag": bool(payload.get("enriched_flag", False)),
            "published_flag": bool(payload.get("published_flag", False)),
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    def _merge_enrichment(self, current: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        updated_at = utc_now_iso()

        def prefer_non_empty(existing: Any, incoming: Any) -> Any:
            if incoming is None:
                return existing
            if isinstance(incoming, str):
                incoming = incoming.strip()
                return incoming or existing
            if isinstance(incoming, list):
                return incoming or existing
            return incoming if incoming not in ("", 0) else existing

        def is_empty_or_unknown(val: Any) -> bool:
            if not val:
                return True
            if isinstance(val, str) and val.strip().lower() in ("", "desconocido", "unknown"):
                return True
            return False

        title = current.get("title", "")
        incoming_title = payload.get("title")
        if is_empty_or_unknown(title) and incoming_title:
            title = str(incoming_title).strip()

        author = current.get("author", "")
        incoming_author = payload.get("author")
        if is_empty_or_unknown(author) and incoming_author:
            author = str(incoming_author).strip()

        publisher = current.get("publisher", "")
        incoming_publisher = payload.get("publisher")
        if is_empty_or_unknown(publisher) and incoming_publisher:
            publisher = str(incoming_publisher).strip()

        description = current["description"]
        incoming_description = str(payload.get("description", "")).strip()
        if is_empty_or_unknown(description) and incoming_description:
            description = incoming_description

        cover_url = prefer_non_empty(current["cover_url"], payload.get("cover_url"))
        summary = prefer_non_empty(current["summary"], payload.get("summary"))
        language = prefer_non_empty(current["language"], payload.get("language"))
        page_count = prefer_non_empty(current["page_count"], payload.get("page_count"))
        published_date = prefer_non_empty(current["published_date"], payload.get("published_date"))
        authors_extra = prefer_non_empty(current["authors_extra"], payload.get("authors_extra", []))
        categories_external = prefer_non_empty(
            current["categories_external"],
            payload.get("categories_external", []),
        )
        thumbnail_url = prefer_non_empty(current["thumbnail_url"], payload.get("thumbnail_url"))
        source_provider = prefer_non_empty(current["source_provider"], payload.get("source_provider"))
        source_reference = prefer_non_empty(current["source_reference"], payload.get("source_reference"))
        enrichment_status = prefer_non_empty(current["enrichment_status"], payload.get("enrichment_status"))

        try:
            enrichment_score = float(payload.get("enrichment_score", current["enrichment_score"]) or 0)
        except (TypeError, ValueError):
            enrichment_score = float(current["enrichment_score"])

        last_enriched_at = payload.get("last_enriched_at") or updated_at
        enriched_flag = bool(
            payload.get("enriched_flag", current["enriched_flag"] or enrichment_status == "completed")
        )
        publication_year = prefer_non_empty(current["publication_year"], payload.get("publication_year"))

        return {
            "title": title,
            "author": author,
            "publisher": publisher,
            "description": description,
            "cover_url": cover_url,
            "summary": summary,
            "language": language,
            "page_count": max(int(page_count or 0), 0),
            "published_date": str(published_date or "").strip(),
            "authors_extra": list(authors_extra or []),
            "categories_external": list(categories_external or []),
            "thumbnail_url": str(thumbnail_url or "").strip(),
            "source_provider": str(source_provider or "").strip(),
            "source_reference": str(source_reference or "").strip(),
            "enrichment_status": str(enrichment_status or "pending").strip(),
            "enrichment_score": enrichment_score,
            "last_enriched_at": str(last_enriched_at).strip(),
            "enriched_flag": enriched_flag,
            "publication_year": publication_year,
            "updated_at": updated_at,
        }

    def _deserialize_book_row(self, row: dict[str, Any]) -> dict[str, Any]:
        row["enriched_flag"] = bool(row["enriched_flag"])
        row["published_flag"] = bool(row["published_flag"])
        row["page_count"] = int(row["page_count"] or 0)
        row["enrichment_score"] = float(row["enrichment_score"] or 0)
        row["suggested_price"] = float(row["suggested_price"]) if row.get("suggested_price") is not None else None
        row["currency"] = str(row.get("currency") or "COP")
        row["price_source"] = str(row.get("price_source") or "")
        row["price_updated_at"] = str(row.get("price_updated_at") or "")
        row["authors_extra"] = self._loads_json_list(row.get("authors_extra"))
        row["categories_external"] = self._loads_json_list(row.get("categories_external"))
        return row

    def _map_book_row(
        self,
        row: dict[str, Any],
        inventory_stats: dict[str, int] | None = None,
        inventory_sync: bool = False,
    ) -> dict[str, Any]:
        row["quantity_available_total"] = inventory_stats["quantity_available_total"] if inventory_stats else 0
        row["quantity_reserved_total"] = inventory_stats["quantity_reserved_total"] if inventory_stats else 0
        row["inventory_records"] = inventory_stats["inventory_records"] if inventory_stats else 0
        row["inventory_sync"] = inventory_sync
        return row

    @staticmethod
    def _build_inventory_index(items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
        index: dict[str, dict[str, int]] = {}
        for item in items:
            ref = str(item.get("book_reference", "")).strip()
            if not ref:
                continue
            if ref not in index:
                index[ref] = {
                    "quantity_available_total": 0,
                    "quantity_reserved_total": 0,
                    "inventory_records": 0,
                }
            index[ref]["quantity_available_total"] += int(item.get("quantity_available", 0))
            index[ref]["quantity_reserved_total"] += int(item.get("quantity_reserved", 0))
            index[ref]["inventory_records"] += 1
        return index

    @staticmethod
    def _loads_json_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if not value:
            return []
        try:
            data = json.loads(value)
        except (TypeError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        return [str(item) for item in data]
