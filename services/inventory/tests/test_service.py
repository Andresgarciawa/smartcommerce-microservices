from __future__ import annotations

import textwrap
import unittest
import os
import uuid
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
        self.prefix = f"TST-{uuid.uuid4().hex[:8]}"

    def tearDown(self) -> None:
        pass

    def test_import_csv_persists_valid_rows_and_tracks_errors(self) -> None:
        csv_content = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            {prefix}-001,BOOK-001,12,2,used_good,,Ingreso inicial
            {prefix}-002,BOOK-002,4,8,used_fair,Portada rota,Reserva inconsistente
            """
        ).strip().format(prefix=self.prefix)

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
        self.assertEqual(items[0]["external_code"], f"{self.prefix}-001")

    def test_import_csv_updates_existing_external_code(self) -> None:
        initial_csv = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            {prefix}-001,BOOK-001,5,1,used_good,,Primer lote
            """
        ).strip().format(prefix=self.prefix)
        updated_csv = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            {prefix}-001,BOOK-001,9,0,new,,Actualizacion
            """
        ).strip().format(prefix=self.prefix)

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
            {prefix}-099,BOOK-404,3,1,used_good,,Libro sin catalogo
            """
        ).strip().format(prefix=self.prefix)

        result = self.service.import_csv("inventory.csv", csv_content)

        self.assertEqual(result["batch"]["status"], "completed_with_errors")
        self.assertEqual(result["batch"]["valid_rows"], 0)
        self.assertEqual(result["batch"]["invalid_rows"], 1)
        self.assertIn("inexistente en Catalog Service", result["errors"][0]["message"])

    def test_delete_item_removes_inventory_record(self) -> None:
        csv_content = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            {prefix}-001,BOOK-001,6,1,used_good,,Ingreso inicial
            """
        ).strip().format(prefix=self.prefix)

        self.service.import_csv("inventory.csv", csv_content)
        item_id = self.service.list_items()[0]["id"]

        self.service.delete_item(item_id)

        self.assertEqual(self.service.get_summary()["total_items"], 0)
        self.assertEqual(self.service.list_items(), [])

    def test_delete_batch_removes_items_and_errors(self) -> None:
        csv_content = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            {prefix}-001,BOOK-001,6,1,used_good,,Ingreso inicial
            {prefix}-002,BOOK-002,4,8,used_fair,Portada rota,Reserva inconsistente
            """
        ).strip().format(prefix=self.prefix)

        result = self.service.import_csv("inventory.csv", csv_content)
        batch_id = result["batch"]["id"]

        self.service.delete_batch(batch_id)

        self.assertEqual(self.service.list_batches(), [])
        self.assertEqual(self.service.list_items(), [])
        with self.assertRaises(ValueError):
            self.service.get_batch_errors(batch_id)

    def test_list_errors_returns_batch_context_and_supports_filters(self) -> None:
        first_csv = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            {prefix}-010,BOOK-404,2,1,used_good,,Referencia invalida
            """
        ).strip().format(prefix=self.prefix)
        second_csv = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            {prefix}-011,BOOK-001,1,3,used_good,,Reserva inconsistente
            """
        ).strip().format(prefix=self.prefix)

        first_result = self.service.import_csv("first.csv", first_csv)
        self.service.import_csv("second.csv", second_csv)

        all_errors = self.service.list_errors()
        validation_errors = self.service.list_errors(error_type="validation_error")
        first_batch_errors = self.service.list_errors(batch_id=first_result["batch"]["id"])

        self.assertGreaterEqual(len(all_errors), 2)
        self.assertTrue(all("file_name" in error for error in all_errors))
        self.assertGreaterEqual(len(validation_errors), 2)
        self.assertEqual(len(first_batch_errors), 1)
        self.assertEqual(first_batch_errors[0]["file_name"], "first.csv")

    def test_quality_summary_aggregates_error_metrics(self) -> None:
        invalid_row_csv = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations
            {prefix}-020,BOOK-404,2,1,used_good,,Referencia invalida
            """
        ).strip().format(prefix=self.prefix)
        invalid_schema_csv = textwrap.dedent(
            """
            external_code,book_reference,quantity_available,condition
            {prefix}-021,BOOK-001,2,used_good
            """
        ).strip().format(prefix=self.prefix)

        self.service.import_csv("row-errors.csv", invalid_row_csv)
        self.service.import_csv("schema-errors.csv", invalid_schema_csv)

        quality = self.service.get_data_quality_summary()

        self.assertGreaterEqual(quality["total_batches"], 2)
        self.assertGreaterEqual(quality["batches_with_errors"], 2)
        self.assertGreaterEqual(quality["failed_batches"], 1)
        self.assertGreaterEqual(quality["total_errors"], 2)
        self.assertTrue(any(item["error_type"] == "schema_error" for item in quality["errors_by_type"]))
        self.assertTrue(any(item["error_type"] == "validation_error" for item in quality["errors_by_type"]))

    def test_get_batch_errors_raises_for_unknown_batch(self) -> None:
        with self.assertRaises(ValueError):
            self.service.get_batch_errors("batch-missing")


if __name__ == "__main__":
    unittest.main()
