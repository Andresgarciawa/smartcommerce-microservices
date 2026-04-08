from __future__ import annotations

import textwrap
import unittest
import os
from dataclasses import dataclass

from services.inventory.catalog_client import CatalogBookLookup
from services.inventory.database import initialize_database
from services.inventory.service import InventoryService


@dataclass
class FakeCatalogClient:
    existing_books: set[str]
    reachable: bool = True

    def get_book(self, book_id: str) -> CatalogBookLookup:
        if not self.reachable:
            return CatalogBookLookup(
                exists=False,
                reachable=False,
                error_message="Catalog Service no disponible.",
            )

        return CatalogBookLookup(
            exists=book_id in self.existing_books,
            reachable=True,
            payload={"id": book_id} if book_id in self.existing_books else None,
            error_message=None
            if book_id in self.existing_books
            else "Libro inexistente.",
        )


class InventoryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.getenv("INVENTORY_TEST_DB", "0") != "1":
            self.skipTest("INVENTORY_TEST_DB=1 requerido para pruebas de integracion con PostgreSQL.")
        initialize_database()
        self.service = InventoryService(
            catalog_client=FakeCatalogClient({"BOOK-001", "BOOK-002"}),
        )

    def tearDown(self) -> None:
        pass

    def test_import_csv_persists_valid_rows_and_tracks_errors(self) -> None:
        csv_content = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            INV-001,BOOK-001,12,2,used_good,,Ingreso inicial
            INV-002,BOOK-002,4,8,used_fair,,Reserva inconsistente
            """
        ).strip()

        result = self.service.import_csv("inventory.csv", csv_content)
        summary = self.service.get_summary()
        items = self.service.list_items()

        self.assertEqual(result["batch"]["processed_rows"], 2)
        self.assertEqual(result["batch"]["valid_rows"], 1)
        self.assertEqual(result["batch"]["invalid_rows"], 1)
        self.assertEqual(result["batch"]["status"], "completed_with_errors")
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(summary["total_items"], 1)
        self.assertEqual(summary["total_batches"], 1)
        self.assertEqual(summary["batches_with_errors"], 1)
        self.assertEqual(items[0]["external_code"], "INV-001")

    def test_import_csv_updates_existing_external_code(self) -> None:
        initial_csv = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            INV-001,BOOK-001,5,1,used_good,,Primer lote
            """
        ).strip()
        updated_csv = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            INV-001,BOOK-001,9,0,new,,Actualizacion
            """
        ).strip()

        self.service.import_csv("batch-a.csv", initial_csv)
        self.service.import_csv("batch-b.csv", updated_csv)
        items = self.service.list_items()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quantity_available"], 9)
        self.assertEqual(items[0]["condition"], "new")

    def test_import_csv_rejects_unknown_catalog_reference(self) -> None:
        csv_content = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            INV-099,BOOK-404,3,1,used_good,,Libro sin catalogo
            """
        ).strip()

        result = self.service.import_csv("inventory.csv", csv_content)

        self.assertEqual(result["batch"]["status"], "completed_with_errors")
        self.assertEqual(result["batch"]["valid_rows"], 0)
        self.assertEqual(result["batch"]["invalid_rows"], 1)
        self.assertIn("inexistente en Catalog Service", result["errors"][0]["message"])

    def test_delete_item_removes_inventory_record(self) -> None:
        csv_content = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            INV-001,BOOK-001,6,1,used_good,,Ingreso inicial
            """
        ).strip()

        self.service.import_csv("inventory.csv", csv_content)
        item_id = self.service.list_items()[0]["id"]

        self.service.delete_item(item_id)

        self.assertEqual(self.service.get_summary()["total_items"], 0)
        self.assertEqual(self.service.list_items(), [])

    def test_delete_batch_removes_items_and_errors(self) -> None:
        csv_content = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            INV-001,BOOK-001,6,1,used_good,,Ingreso inicial
            INV-002,BOOK-002,4,8,used_fair,,Reserva inconsistente
            """
        ).strip()

        result = self.service.import_csv("inventory.csv", csv_content)
        batch_id = result["batch"]["id"]

        self.service.delete_batch(batch_id)

        self.assertEqual(self.service.list_batches(), [])
        self.assertEqual(self.service.list_items(), [])
        self.assertEqual(self.service.get_batch_errors(batch_id), [])


if __name__ == "__main__":
    unittest.main()
