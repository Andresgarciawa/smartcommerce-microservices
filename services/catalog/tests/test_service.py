from __future__ import annotations

import unittest
from dataclasses import dataclass
from pathlib import Path
import uuid

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
        base_dir = Path(__file__).resolve().parent
        self.temp_dir = base_dir
        self.db_path = base_dir / f"catalog-test-{uuid.uuid4().hex}.db"
        self.inventory_client = FakeInventoryClient()
        self.service = CatalogService(
            sqlite_path=str(self.db_path),
            inventory_client=self.inventory_client,
        )

    def tearDown(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()

    def _create_book(self, *, title: str = "Cien anos de soledad", enriched: bool = False) -> dict[str, object]:
        category = self.service.create_category("Novela", "Ficcion narrativa")
        return self.service.create_book(
            {
                "title": title,
                "subtitle": "",
                "author": "Gabriel Garcia Marquez",
                "publisher": "Sudamericana",
                "publication_year": 1967,
                "volume": "",
                "isbn": "123",
                "issn": "",
                "category_id": category["id"],
                "description": "",
                "cover_url": "",
                "enriched_flag": enriched,
                "published_flag": True,
            }
        )

    def test_create_category_and_book_updates_summary(self) -> None:
        book = self._create_book(enriched=True)
        summary = self.service.get_summary()

        self.assertEqual(summary["total_categories"], 1)
        self.assertEqual(summary["total_books"], 1)
        self.assertEqual(summary["published_books"], 1)
        self.assertEqual(summary["enriched_books"], 1)
        self.assertEqual(book["category_name"], "Novela")

    def test_create_book_requires_at_least_one_identifier(self) -> None:
        category = self.service.create_category("Referencia", "")

        with self.assertRaisesRegex(ValueError, "isbn o issn"):
            self.service.create_book(
                {
                    "title": "Libro sin identificador",
                    "author": "Autor",
                    "publisher": "Editorial",
                    "publication_year": 2020,
                    "isbn": "",
                    "issn": "",
                    "category_id": category["id"],
                }
            )

    def test_create_book_accepts_issn_without_isbn(self) -> None:
        category = self.service.create_category("Revista", "")

        book = self.service.create_book(
            {
                "title": "Revista cultural",
                "author": "Equipo editorial",
                "publisher": "Editorial",
                "publication_year": 2020,
                "isbn": "",
                "issn": "1234-5678",
                "category_id": category["id"],
            }
        )

        self.assertEqual(book["isbn"], "")
        self.assertEqual(book["issn"], "1234-5678")

    def test_list_books_includes_inventory_aggregation(self) -> None:
        book = self._create_book(title="Historia minima")
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

    def test_apply_enrichment_updates_commercial_fields(self) -> None:
        book = self._create_book()

        enriched = self.service.apply_enrichment(
            str(book["id"]),
            {
                "summary": "Novela sobre Macondo.",
                "language": "es",
                "page_count": 496,
                "published_date": "1967-05-30",
                "authors_extra": ["Gabo"],
                "categories_external": ["Realismo magico"],
                "thumbnail_url": "https://img.test/macondo-small.jpg",
                "cover_url": "https://img.test/macondo.jpg",
                "source_provider": "google_books",
                "source_reference": "GB-123",
                "enrichment_status": "completed",
                "enrichment_score": 0.91,
            },
        )

        self.assertTrue(enriched["enriched_flag"])
        self.assertEqual(enriched["summary"], "Novela sobre Macondo.")
        self.assertEqual(enriched["language"], "es")
        self.assertEqual(enriched["page_count"], 496)
        self.assertEqual(enriched["categories_external"], ["Realismo magico"])
        self.assertEqual(enriched["source_provider"], "google_books")
        self.assertEqual(enriched["enrichment_status"], "completed")

    def test_apply_enrichment_keeps_existing_description_when_payload_is_empty(self) -> None:
        category = self.service.create_category("Ensayo", "")
        book = self.service.create_book(
            {
                "title": "Ensayo",
                "author": "Autor",
                "publisher": "Editorial",
                "publication_year": 2021,
                "isbn": "555-TEST",
                "category_id": category["id"],
                "description": "Descripcion base",
            }
        )

        enriched = self.service.apply_enrichment(
            str(book["id"]),
            {
                "description": "",
                "summary": "Resumen nuevo",
                "enrichment_status": "completed",
            },
        )

        self.assertEqual(enriched["description"], "Descripcion base")
        self.assertEqual(enriched["summary"], "Resumen nuevo")

    def test_list_books_supports_enriched_filter_and_search(self) -> None:
        self._create_book(title="Libro sin enriquecer", enriched=False)
        category = self.service.list_categories()[0]
        second = self.service.create_book(
            {
                "title": "Libro enriquecido",
                "author": "Otra autora",
                "publisher": "Editorial",
                "publication_year": 2019,
                "isbn": "ABC-999",
                "category_id": category["id"],
                "enriched_flag": True,
                "published_flag": True,
            }
        )
        self.service.apply_enrichment(
            str(second["id"]),
            {
                "summary": "Ficha comercial",
                "enrichment_status": "completed",
                "source_provider": "open_library",
            },
        )

        enriched_books = self.service.list_books(enriched_only=True)
        searched_books = self.service.list_books(q="abc-999")

        self.assertEqual(len(enriched_books), 1)
        self.assertEqual(enriched_books[0]["title"], "Libro enriquecido")
        self.assertEqual(len(searched_books), 1)
        self.assertEqual(searched_books[0]["isbn"], "ABC-999")

    def test_delete_category_fails_when_books_exist(self) -> None:
        self._create_book(title="Poemas")

        category = self.service.list_categories()[0]
        with self.assertRaisesRegex(ValueError, "tiene libros asociados"):
            self.service.delete_category(str(category["id"]))

    def test_delete_book_fails_when_inventory_exists(self) -> None:
        book = self._create_book(title="Inventariado")
        self.inventory_client.items = [
            {
                "id": "INV-1",
                "book_reference": book["id"],
                "quantity_available": 5,
                "quantity_reserved": 0,
            }
        ]

        with self.assertRaisesRegex(ValueError, "inventario asociado"):
            self.service.delete_book(str(book["id"]))

    def test_delete_book_succeeds_without_inventory(self) -> None:
        book = self._create_book(title="Cuentos")

        self.service.delete_book(str(book["id"]))

        self.assertEqual(self.service.list_books(), [])


if __name__ == "__main__":
    unittest.main()
