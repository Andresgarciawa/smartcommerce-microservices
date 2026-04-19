from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .database import get_connection, initialize_database
from .inventory_client import InventoryClient


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
        query = """
                INSERT INTO books (
                    id, title, subtitle, author, publisher, publication_year,
                    volume, isbn, issn, category_id, description, cover_url,
                    enriched_flag, published_flag, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    book["id"], book["title"], book["subtitle"], book["author"],
                    book["publisher"], book["publication_year"], book["volume"],
                    book["isbn"], book["issn"], book["category_id"],
                    book["description"], book["cover_url"], book["enriched_flag"],
                    book["published_flag"], book["created_at"], book["updated_at"],
                ))
            connection.commit()
        return self.get_book(book["id"])

    def list_books(self) -> list[dict[str, Any]]:
        query = """
                SELECT books.id, books.title, books.subtitle, books.author,
                       books.publisher, books.publication_year, books.volume,
                       books.isbn, books.issn, books.category_id,
                       categories.name AS category_name, books.description,
                       books.cover_url, books.enriched_flag, books.published_flag
                FROM books
                         JOIN categories ON categories.id = books.category_id
                ORDER BY books.updated_at DESC, books.title ASC \
                """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
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
                       books.cover_url, books.enriched_flag, books.published_flag
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

    def _validate_book_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
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
        current_year = 2026
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
            "isbn": str(payload.get("isbn", "")).strip(),
            "issn": str(payload.get("issn", "")).strip(),
            "category_id": category_id,
            "description": str(payload.get("description", "")).strip(),
            "cover_url": str(payload.get("cover_url", "")).strip(),
            "enriched_flag": bool(payload.get("enriched_flag", False)),
            "published_flag": bool(payload.get("published_flag", False)),
            "created_at": timestamp,
            "updated_at": timestamp,
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