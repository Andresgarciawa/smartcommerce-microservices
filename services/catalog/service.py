from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .database import get_connection, initialize_database
from .inventory_client import InventoryClient

PUBLISH_REQUIRED_FIELDS = ("title", "author", "publisher", "publication_year", "category_id")
CRITICAL_FIELDS = {
    "title",
    "subtitle",
    "author",
    "publisher",
    "publication_year",
    "isbn",
    "issn",
    "category_id",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_dict(cursor, row) -> dict[str, Any]:
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


class CatalogService:
    def __init__(self, inventory_client: InventoryClient | None = None) -> None:
        initialize_database()
        self.inventory_client = inventory_client or InventoryClient(
            os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:8000")
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
        query = """
                INSERT INTO categories (id, name, description, created_at)
                VALUES (%s, %s, %s, %s) \
                """
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (
                        category["id"], category["name"],
                        category["description"], category["created_at"],
                    ))
                connection.commit()
        except Exception as error:
            if "unique" in str(error).lower():
                raise ValueError("Ya existe una categoria con ese nombre.") from error
            raise
        return self.get_category(category["id"])

    def list_categories(self) -> list[dict[str, Any]]:
        query = "SELECT id, name, description, created_at FROM categories ORDER BY name ASC"
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return [row_to_dict(cursor, row) for row in rows]

    def get_category(self, category_id: str) -> dict[str, Any]:
        query = "SELECT id, name, description, created_at FROM categories WHERE id = %s"
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (category_id,))
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("La categoria solicitada no existe.")
                return row_to_dict(cursor, row)

    def create_book(self, payload: dict[str, Any]) -> dict[str, Any]:
        book = self._validate_book_payload(payload)
        if book["published_flag"]:
            self._ensure_publishable(book)
        query = """
                INSERT INTO books (
                    id, title, subtitle, author, publisher, publication_year,
                    volume, isbn, issn, category_id, description, cover_url,
                    enriched_flag, published_flag, created_at, updated_at,
                    suggested_price, currency, price_source, price_updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    book["id"], book["title"], book["subtitle"], book["author"],
                    book["publisher"], book["publication_year"], book["volume"],
                    book["isbn"], book["issn"], book["category_id"],
                    book["description"], book["cover_url"], book["enriched_flag"],
                    book["published_flag"], book["created_at"], book["updated_at"],
                    book["suggested_price"], book["currency"],
                    book["price_source"], book["price_updated_at"],
                ))
            connection.commit()
        return self.get_book(book["id"])

    def list_books(
        self,
        query_text: str | None = None,
        category_id: str | None = None,
        published: bool | None = None,
        enriched: bool | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        filters = []
        params: list[Any] = []
        if query_text:
            query_value = f"%{query_text.strip()}%"
            filters.append("""
                (books.title ILIKE %s OR books.subtitle ILIKE %s OR books.author ILIKE %s
                 OR books.publisher ILIKE %s OR books.isbn ILIKE %s OR books.issn ILIKE %s
                 OR books.description ILIKE %s)
            """)
            params.extend([query_value] * 7)
        if category_id:
            filters.append("books.category_id = %s")
            params.append(category_id)
        if published is not None:
            filters.append("books.published_flag = %s")
            params.append(published)
        if enriched is not None:
            filters.append("books.enriched_flag = %s")
            params.append(enriched)
        if year_from is not None:
            filters.append("books.publication_year >= %s")
            params.append(year_from)
        if year_to is not None:
            filters.append("books.publication_year <= %s")
            params.append(year_to)

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""
        query = """
                SELECT books.id, books.title, books.subtitle, books.author,
                       books.publisher, books.publication_year, books.volume,
                       books.isbn, books.issn, books.category_id,
                       categories.name AS category_name, books.description,
                       books.cover_url, books.enriched_flag, books.published_flag,
                       books.suggested_price, books.currency, books.price_source,
                       books.price_updated_at, books.created_at, books.updated_at
                FROM books
                         JOIN categories ON categories.id = books.category_id
                {where_clause}
                ORDER BY books.updated_at DESC, books.title ASC
                LIMIT %s OFFSET %s \
                """
        params.extend([limit, offset])
        query = query.format(where_clause=where_clause)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                result = [row_to_dict(cursor, row) for row in rows]

        inventory_snapshot = self.inventory_client.list_items()
        inventory_index = self._build_inventory_index(inventory_snapshot.items)
        return [
            self._map_book_row(row,
                               inventory_stats=inventory_index.get(row["id"]),
                               inventory_sync=inventory_snapshot.reachable)
            for row in result
        ]

    def get_book(self, book_id: str) -> dict[str, Any]:
        query = """
                SELECT books.id, books.title, books.subtitle, books.author,
                       books.publisher, books.publication_year, books.volume,
                       books.isbn, books.issn, books.category_id,
                       categories.name AS category_name, books.description,
                       books.cover_url, books.enriched_flag, books.published_flag,
                       books.suggested_price, books.currency, books.price_source,
                       books.price_updated_at, books.created_at, books.updated_at
                FROM books
                         JOIN categories ON categories.id = books.category_id
                WHERE books.id = %s \
                """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (book_id,))
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("El libro solicitado no existe.")
                result = row_to_dict(cursor, row)

        inventory_snapshot = self.inventory_client.list_items()
        inventory_index = self._build_inventory_index(inventory_snapshot.items)
        return self._map_book_row(result,
                                  inventory_stats=inventory_index.get(result["id"]),
                                  inventory_sync=inventory_snapshot.reachable)

    def get_summary(self) -> dict[str, int]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM categories")
                total_categories = cursor.fetchone()[0]
                cursor.execute("""
                               SELECT COUNT(*),
                                      COALESCE(SUM(CASE WHEN published_flag THEN 1 ELSE 0 END), 0),
                                      COALESCE(SUM(CASE WHEN enriched_flag THEN 1 ELSE 0 END), 0)
                               FROM books
                               """)
                row = cursor.fetchone()
        return {
            "total_categories": total_categories,
            "total_books": row[0],
            "published_books": row[1],
            "enriched_books": row[2],
        }

    def delete_category(self, category_id: str) -> None:
        self.get_category(category_id)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM books WHERE category_id = %s", (category_id,))
                count = cursor.fetchone()[0]
                if count > 0:
                    raise ValueError("No se puede eliminar la categoria porque tiene libros asociados.")
                cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
            connection.commit()

    def delete_book(self, book_id: str) -> None:
        self.get_book(book_id)
        inventory_snapshot = self.inventory_client.list_items()
        linked = [i for i in inventory_snapshot.items
                  if str(i.get("book_reference", "")).strip() == book_id]
        if inventory_snapshot.reachable and linked:
            raise ValueError("No se puede eliminar el libro porque tiene inventario asociado.")
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
            connection.commit()

    def update_book(self, book_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        book = self.get_book(book_id)
        update_payload = self._sanitize_update_payload(payload)
        update_payload = self._preserve_identifiers(book, update_payload)
        if "category_id" in update_payload:
            self.get_category(update_payload["category_id"])
        updated = self._apply_updates(book, update_payload)
        self._persist_book_updates(book_id, updated)
        return self.get_book(book_id)

    def publish_book(self, book_id: str) -> dict[str, Any]:
        book = self.get_book(book_id)
        self._ensure_publishable(book)
        update_payload = {
            "published_flag": True,
            "updated_at": utc_now_iso(),
        }
        self._persist_book_updates(book_id, update_payload)
        return self.get_book(book_id)

    def enrich_book(self, book_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        source = str(payload.get("source", "")).strip()
        if not source:
            raise ValueError("source es obligatorio para enriquecer el libro.")
        book = self.get_book(book_id)
        update_payload = self._sanitize_update_payload(payload)
        update_payload = self._preserve_identifiers(book, update_payload)
        if "category_id" in update_payload:
            self.get_category(update_payload["category_id"])
        changes = self._detect_changes(book, update_payload, CRITICAL_FIELDS)
        for field_name, old_value, new_value in changes:
            self._log_change(book_id, field_name, old_value, new_value, source)
        update_payload = self._apply_updates(book, update_payload)
        update_payload["enriched_flag"] = True
        update_payload["updated_at"] = utc_now_iso()
        self._persist_book_updates(book_id, update_payload)
        return self.get_book(book_id)

    def _validate_book_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        supplied_id = payload.get("id")
        title = str(payload.get("title", "")).strip()
        author = str(payload.get("author", "")).strip()
        publisher = str(payload.get("publisher", "")).strip()
        category_id = str(payload.get("category_id", "")).strip()
        if not title:
            raise ValueError("title es obligatorio.")
        if not author:
            raise ValueError("author es obligatorio.")
        if not publisher:
            raise ValueError("publisher es obligatorio.")
        if not category_id:
            raise ValueError("category_id es obligatorio.")
        self.get_category(category_id)
        try:
            publication_year = int(payload.get("publication_year", 0))
        except (TypeError, ValueError) as error:
            raise ValueError("publication_year debe ser numerico.") from error
        current_year = datetime.now(timezone.utc).year + 1
        if publication_year < 1000 or publication_year > current_year:
            raise ValueError("publication_year esta fuera de rango.")
        timestamp = utc_now_iso()
        suggested_price = payload.get("suggested_price")
        if suggested_price is not None:
            try:
                suggested_price = float(suggested_price)
            except (TypeError, ValueError) as error:
                raise ValueError("suggested_price debe ser numerico.") from error
        price_source = str(payload.get("price_source", "")).strip()
        currency = str(payload.get("currency", "COP")).strip() or "COP"
        price_updated_at = timestamp if suggested_price is not None else None
        return {
            "id": str(supplied_id).strip() if supplied_id else str(uuid.uuid4()),
            "title": title,
            "subtitle": str(payload.get("subtitle", "")).strip(),
            "author": author,
            "publisher": publisher,
            "publication_year": publication_year,
            "volume": str(payload.get("volume", "")).strip(),
            "isbn": str(payload.get("isbn", "")).strip(),
            "issn": str(payload.get("issn", "")).strip(),
            "category_id": category_id,
            "description": str(payload.get("description", "")).strip(),
            "cover_url": str(payload.get("cover_url", "")).strip(),
            "enriched_flag": bool(payload.get("enriched_flag", False)),
            "published_flag": bool(payload.get("published_flag", False)),
            "created_at": timestamp,
            "updated_at": timestamp,
            "suggested_price": suggested_price,
            "currency": currency,
            "price_source": price_source,
            "price_updated_at": price_updated_at,
        }

    def _map_book_row(self, row, inventory_stats=None, inventory_sync=False):
        row["enriched_flag"] = bool(row["enriched_flag"])
        row["published_flag"] = bool(row["published_flag"])
        row["quantity_available_total"] = inventory_stats["quantity_available_total"] if inventory_stats else 0
        row["quantity_reserved_total"] = inventory_stats["quantity_reserved_total"] if inventory_stats else 0
        row["inventory_records"] = inventory_stats["inventory_records"] if inventory_stats else 0
        row["inventory_sync"] = inventory_sync
        return row

    @staticmethod
    def _build_inventory_index(items):
        index = {}
        for item in items:
            ref = str(item.get("book_reference", "")).strip()
            if not ref:
                continue
            if ref not in index:
                index[ref] = {"quantity_available_total": 0, "quantity_reserved_total": 0, "inventory_records": 0}
            index[ref]["quantity_available_total"] += int(item.get("quantity_available", 0))
            index[ref]["quantity_reserved_total"] += int(item.get("quantity_reserved", 0))
            index[ref]["inventory_records"] += 1
        return index

    def _sanitize_update_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        allowed_fields = {
            "title",
            "subtitle",
            "author",
            "publisher",
            "publication_year",
            "volume",
            "isbn",
            "issn",
            "category_id",
            "description",
            "cover_url",
            "suggested_price",
            "currency",
            "price_source",
        }
        update_payload = {}
        for key, value in payload.items():
            if key in allowed_fields:
                update_payload[key] = value
        if "currency" in update_payload and update_payload["currency"] is not None:
            currency = str(update_payload["currency"]).strip()
            update_payload["currency"] = currency or None
        if "price_source" in update_payload and update_payload["price_source"] is not None:
            update_payload["price_source"] = str(update_payload["price_source"]).strip()
        if "publication_year" in update_payload and update_payload["publication_year"] is not None:
            try:
                update_payload["publication_year"] = int(update_payload["publication_year"])
            except (TypeError, ValueError) as error:
                raise ValueError("publication_year debe ser numerico.") from error
        if "suggested_price" in update_payload and update_payload["suggested_price"] is not None:
            try:
                update_payload["suggested_price"] = float(update_payload["suggested_price"])
            except (TypeError, ValueError) as error:
                raise ValueError("suggested_price debe ser numerico.") from error
        return update_payload

    @staticmethod
    def _preserve_identifiers(existing: dict[str, Any], update_payload: dict[str, Any]) -> dict[str, Any]:
        for field_name in ("isbn", "issn"):
            current_value = str(existing.get(field_name, "")).strip()
            incoming_value = update_payload.get(field_name)
            if current_value:
                if incoming_value is None:
                    continue
                incoming_value = str(incoming_value).strip()
                if incoming_value and incoming_value != current_value:
                    update_payload[field_name] = current_value
                elif not incoming_value:
                    update_payload[field_name] = current_value
        return update_payload

    @staticmethod
    def _apply_updates(existing: dict[str, Any], update_payload: dict[str, Any]) -> dict[str, Any]:
        updated = {}
        for key, value in update_payload.items():
            if value is None:
                continue
            updated[key] = value
        if updated:
            updated["updated_at"] = utc_now_iso()
        if "suggested_price" in updated:
            updated["price_updated_at"] = utc_now_iso()
        return updated

    @staticmethod
    def _detect_changes(existing: dict[str, Any], update_payload: dict[str, Any], fields: set[str]):
        changes = []
        for field_name in fields:
            if field_name not in update_payload:
                continue
            incoming = update_payload[field_name]
            if incoming is None:
                continue
            current_value = existing.get(field_name)
            if str(current_value) != str(incoming):
                changes.append((field_name, str(current_value), str(incoming)))
        return changes

    def _log_change(self, book_id: str, field_name: str, old_value: str, new_value: str, source: str) -> None:
        query = """
                INSERT INTO book_change_log (id, book_id, field_name, old_value, new_value, source, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    str(uuid.uuid4()),
                    book_id,
                    field_name,
                    old_value,
                    new_value,
                    source,
                    utc_now_iso(),
                ))
            connection.commit()

    def _persist_book_updates(self, book_id: str, update_payload: dict[str, Any]) -> None:
        if not update_payload:
            return
        set_clauses = []
        values = []
        for key, value in update_payload.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        values.append(book_id)
        query = f"UPDATE books SET {', '.join(set_clauses)} WHERE id = %s"
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)
            connection.commit()

    @staticmethod
    def _missing_publish_fields(book: dict[str, Any]) -> list[str]:
        missing = []
        for field_name in PUBLISH_REQUIRED_FIELDS:
            value = book.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field_name)
        return missing

    def _ensure_publishable(self, book: dict[str, Any]) -> None:
        missing = self._missing_publish_fields(book)
        if missing:
            fields = ", ".join(missing)
            raise ValueError(f"No se puede publicar. Faltan campos requeridos: {fields}.")
