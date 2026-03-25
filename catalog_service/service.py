from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .database import DEFAULT_DB_PATH, get_connection, initialize_database
from .inventory_client import InventoryClient


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


class CatalogService:
    def __init__(
        self,
        db_path: Path = DEFAULT_DB_PATH,
        inventory_client: InventoryClient | None = None,
    ) -> None:
        self.db_path = db_path
        initialize_database(self.db_path)
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
        VALUES (?, ?, ?, ?)
        """

        try:
            with get_connection(self.db_path) as connection:
                connection.execute(
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
            if "UNIQUE constraint failed" in str(error):
                raise ValueError("Ya existe una categoria con ese nombre.") from error
            raise

        return self.get_category(category["id"])

    def list_categories(self) -> list[dict[str, Any]]:
        query = """
        SELECT id, name, description, created_at
        FROM categories
        ORDER BY name ASC
        """

        with get_connection(self.db_path) as connection:
            rows = connection.execute(query).fetchall()

        return [row_to_dict(row) for row in rows]

    def get_category(self, category_id: str) -> dict[str, Any]:
        query = """
        SELECT id, name, description, created_at
        FROM categories
        WHERE id = ?
        """

        with get_connection(self.db_path) as connection:
            row = connection.execute(query, (category_id,)).fetchone()

        if row is None:
            raise ValueError("La categoria solicitada no existe.")

        return row_to_dict(row)

    def create_book(self, payload: dict[str, Any]) -> dict[str, Any]:
        book = self._validate_book_payload(payload)

        query = """
        INSERT INTO books (
            id,
            title,
            subtitle,
            author,
            publisher,
            publication_year,
            volume,
            isbn,
            issn,
            category_id,
            description,
            cover_url,
            enriched_flag,
            published_flag,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with get_connection(self.db_path) as connection:
            connection.execute(
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
                    book["enriched_flag"],
                    book["published_flag"],
                    book["created_at"],
                    book["updated_at"],
                ),
            )
            connection.commit()

        return self.get_book(book["id"])

    def list_books(self) -> list[dict[str, Any]]:
        query = """
        SELECT
            books.id,
            books.title,
            books.subtitle,
            books.author,
            books.publisher,
            books.publication_year,
            books.volume,
            books.isbn,
            books.issn,
            books.category_id,
            categories.name AS category_name,
            books.description,
            books.cover_url,
            books.enriched_flag,
            books.published_flag
        FROM books
        JOIN categories ON categories.id = books.category_id
        ORDER BY books.updated_at DESC, books.title ASC
        """

        with get_connection(self.db_path) as connection:
            rows = connection.execute(query).fetchall()

        inventory_snapshot = self.inventory_client.list_items()
        inventory_index = self._build_inventory_index(inventory_snapshot.items)

        return [
            self._map_book_row(
                row,
                inventory_stats=inventory_index.get(row["id"]),
                inventory_sync=inventory_snapshot.reachable,
            )
            for row in rows
        ]

    def get_book(self, book_id: str) -> dict[str, Any]:
        query = """
        SELECT
            books.id,
            books.title,
            books.subtitle,
            books.author,
            books.publisher,
            books.publication_year,
            books.volume,
            books.isbn,
            books.issn,
            books.category_id,
            categories.name AS category_name,
            books.description,
            books.cover_url,
            books.enriched_flag,
            books.published_flag
        FROM books
        JOIN categories ON categories.id = books.category_id
        WHERE books.id = ?
        """

        with get_connection(self.db_path) as connection:
            row = connection.execute(query, (book_id,)).fetchone()

        if row is None:
            raise ValueError("El libro solicitado no existe.")

        inventory_snapshot = self.inventory_client.list_items()
        inventory_index = self._build_inventory_index(inventory_snapshot.items)
        return self._map_book_row(
            row,
            inventory_stats=inventory_index.get(row["id"]),
            inventory_sync=inventory_snapshot.reachable,
        )

    def get_summary(self) -> dict[str, int]:
        category_query = "SELECT COUNT(*) AS total_categories FROM categories"
        book_query = """
        SELECT
            COUNT(*) AS total_books,
            COALESCE(SUM(CASE WHEN published_flag = 1 THEN 1 ELSE 0 END), 0) AS published_books,
            COALESCE(SUM(CASE WHEN enriched_flag = 1 THEN 1 ELSE 0 END), 0) AS enriched_books
        FROM books
        """

        with get_connection(self.db_path) as connection:
            category_row = connection.execute(category_query).fetchone()
            book_row = connection.execute(book_query).fetchone()

        return {
            "total_categories": int(category_row["total_categories"]),
            "total_books": int(book_row["total_books"]),
            "published_books": int(book_row["published_books"]),
            "enriched_books": int(book_row["enriched_books"]),
        }

    def delete_category(self, category_id: str) -> None:
        self.get_category(category_id)

        with get_connection(self.db_path) as connection:
            books_count = connection.execute(
                "SELECT COUNT(*) AS total FROM books WHERE category_id = ?",
                (category_id,),
            ).fetchone()

            if int(books_count["total"]) > 0:
                raise ValueError(
                    "No se puede eliminar la categoria porque tiene libros asociados."
                )

            connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            connection.commit()

    def delete_book(self, book_id: str) -> None:
        self.get_book(book_id)

        inventory_snapshot = self.inventory_client.list_items()
        linked_inventory = [
            item
            for item in inventory_snapshot.items
            if str(item.get("book_reference", "")).strip() == book_id
        ]

        if inventory_snapshot.reachable and linked_inventory:
            raise ValueError(
                "No se puede eliminar el libro porque tiene inventario asociado."
            )

        with get_connection(self.db_path) as connection:
            connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
            connection.commit()

    def _validate_book_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = str(payload.get("title", "")).strip()
        subtitle = str(payload.get("subtitle", "")).strip()
        author = str(payload.get("author", "")).strip()
        publisher = str(payload.get("publisher", "")).strip()
        volume = str(payload.get("volume", "")).strip()
        isbn = str(payload.get("isbn", "")).strip()
        issn = str(payload.get("issn", "")).strip()
        category_id = str(payload.get("category_id", "")).strip()
        description = str(payload.get("description", "")).strip()
        cover_url = str(payload.get("cover_url", "")).strip()
        enriched_flag = bool(payload.get("enriched_flag", False))
        published_flag = bool(payload.get("published_flag", False))

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

        return {
            "id": str(uuid.uuid4()),
            "title": title,
            "subtitle": subtitle,
            "author": author,
            "publisher": publisher,
            "publication_year": publication_year,
            "volume": volume,
            "isbn": isbn,
            "issn": issn,
            "category_id": category_id,
            "description": description,
            "cover_url": cover_url,
            "enriched_flag": 1 if enriched_flag else 0,
            "published_flag": 1 if published_flag else 0,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    def _map_book_row(
        self,
        row: Any,
        inventory_stats: dict[str, int] | None = None,
        inventory_sync: bool = False,
    ) -> dict[str, Any]:
        mapped = row_to_dict(row)
        mapped["enriched_flag"] = bool(mapped["enriched_flag"])
        mapped["published_flag"] = bool(mapped["published_flag"])
        mapped["quantity_available_total"] = (
            inventory_stats["quantity_available_total"] if inventory_stats else 0
        )
        mapped["quantity_reserved_total"] = (
            inventory_stats["quantity_reserved_total"] if inventory_stats else 0
        )
        mapped["inventory_records"] = (
            inventory_stats["inventory_records"] if inventory_stats else 0
        )
        mapped["inventory_sync"] = inventory_sync
        return mapped

    @staticmethod
    def _build_inventory_index(
        items: list[dict[str, Any]]
    ) -> dict[str, dict[str, int]]:
        inventory_index: dict[str, dict[str, int]] = {}

        for item in items:
            book_reference = str(item.get("book_reference", "")).strip()
            if not book_reference:
                continue

            if book_reference not in inventory_index:
                inventory_index[book_reference] = {
                    "quantity_available_total": 0,
                    "quantity_reserved_total": 0,
                    "inventory_records": 0,
                }

            inventory_index[book_reference]["quantity_available_total"] += int(
                item.get("quantity_available", 0)
            )
            inventory_index[book_reference]["quantity_reserved_total"] += int(
                item.get("quantity_reserved", 0)
            )
            inventory_index[book_reference]["inventory_records"] += 1

        return inventory_index
