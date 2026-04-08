from __future__ import annotations

import unittest
import os
from dataclasses import dataclass

from services.catalog.database import initialize_database
from services.catalog.service import CatalogService


@dataclass
class FakeInventorySnapshot:
    reachable: bool
    items: list[dict[str, object]]
    error_message: str | None = None


class FakeInventoryClient:
    def __init__(self, items: list[dict[str, object]] | None = None) -> None:
        self.items = items or []
        self.reachable = True

    def list_items(self) -> FakeInventorySnapshot:
        return FakeInventorySnapshot(
            reachable=self.reachable,
            items=self.items,
        )


class CatalogServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.getenv("CATALOG_TEST_DB", "0") != "1":
            self.skipTest("CATALOG_TEST_DB=1 requerido para pruebas de integracion con PostgreSQL.")
        initialize_database()
        self.inventory_client = FakeInventoryClient()
        self.service = CatalogService(
            inventory_client=self.inventory_client,
        )

    def tearDown(self) -> None:
        pass

    def test_create_category_and_book_updates_summary(self) -> None:
        category = self.service.create_category("Novela", "Ficcion narrativa")
        book = self.service.create_book(
            {
                "title": "Cien anos de soledad",
                "subtitle": "",
                "author": "Gabriel Garcia Marquez",
                "publisher": "Sudamericana",
                "publication_year": 1967,
                "volume": "",
                "isbn": "123",
                "issn": "",
                "category_id": category["id"],
                "description": "Clasico latinoamericano",
                "cover_url": "",
                "enriched_flag": True,
                "published_flag": True,
            }
        )
        summary = self.service.get_summary()

        self.assertEqual(summary["total_categories"], 1)
        self.assertEqual(summary["total_books"], 1)
        self.assertEqual(summary["published_books"], 1)
        self.assertEqual(book["category_name"], "Novela")

    def test_list_books_includes_inventory_aggregation(self) -> None:
        category = self.service.create_category("Historia", "")
        book = self.service.create_book(
            {
                "title": "Historia minima",
                "subtitle": "",
                "author": "Autor",
                "publisher": "Editorial",
                "publication_year": 2019,
                "volume": "",
                "isbn": "",
                "issn": "",
                "category_id": category["id"],
                "description": "",
                "cover_url": "",
                "enriched_flag": False,
                "published_flag": False,
            }
        )
        self.inventory_client.items = [
            {
                "id": "INV-1",
                "book_reference": book["id"],
                "quantity_available": 7,
                "quantity_reserved": 2,
            },
            {
                "id": "INV-2",
                "book_reference": book["id"],
                "quantity_available": 3,
                "quantity_reserved": 1,
            },
        ]

        listed_book = self.service.list_books()[0]

        self.assertEqual(listed_book["quantity_available_total"], 10)
        self.assertEqual(listed_book["quantity_reserved_total"], 3)
        self.assertEqual(listed_book["inventory_records"], 2)
        self.assertTrue(listed_book["inventory_sync"])

    def test_delete_category_fails_when_books_exist(self) -> None:
        category = self.service.create_category("Poesia", "")
        self.service.create_book(
            {
                "title": "Poemas",
                "subtitle": "",
                "author": "Autor",
                "publisher": "Editorial",
                "publication_year": 2020,
                "volume": "",
                "isbn": "",
                "issn": "",
                "category_id": category["id"],
                "description": "",
                "cover_url": "",
                "enriched_flag": False,
                "published_flag": False,
            }
        )

        with self.assertRaisesRegex(ValueError, "tiene libros asociados"):
            self.service.delete_category(category["id"])

    def test_delete_book_fails_when_inventory_exists(self) -> None:
        category = self.service.create_category("Ensayo", "")
        book = self.service.create_book(
            {
                "title": "Ensayo",
                "subtitle": "",
                "author": "Autor",
                "publisher": "Editorial",
                "publication_year": 2021,
                "volume": "",
                "isbn": "",
                "issn": "",
                "category_id": category["id"],
                "description": "",
                "cover_url": "",
                "enriched_flag": False,
                "published_flag": False,
            }
        )
        self.inventory_client.items = [
            {
                "id": "INV-1",
                "book_reference": book["id"],
                "quantity_available": 5,
                "quantity_reserved": 0,
            }
        ]

        with self.assertRaisesRegex(ValueError, "inventario asociado"):
            self.service.delete_book(book["id"])

    def test_delete_book_succeeds_without_inventory(self) -> None:
        category = self.service.create_category("Cuento", "")
        book = self.service.create_book(
            {
                "title": "Cuentos",
                "subtitle": "",
                "author": "Autor",
                "publisher": "Editorial",
                "publication_year": 2018,
                "volume": "",
                "isbn": "",
                "issn": "",
                "category_id": category["id"],
                "description": "",
                "cover_url": "",
                "enriched_flag": False,
                "published_flag": False,
            }
        )

        self.service.delete_book(book["id"])

        self.assertEqual(self.service.list_books(), [])


if __name__ == "__main__":
    unittest.main()
