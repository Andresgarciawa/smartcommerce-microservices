from __future__ import annotations

import csv
import io
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .catalog_client import CatalogClient
from .database import get_connection, initialize_database

REQUIRED_COLUMNS = {
    "external_code",
    "book_reference",
    "quantity_available",
    "quantity_reserved",
    "condition",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_dict(cursor, row) -> dict[str, Any]:
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


class InventoryService:
    def __init__(
        self,
        catalog_client: CatalogClient | None = None,
    ) -> None:
        initialize_database()
        self.catalog_client = catalog_client or CatalogClient(
            os.getenv("CATALOG_SERVICE_URL", "http://127.0.0.1:8001")
        )

    def import_csv(self, file_name: str, csv_content: str) -> dict[str, Any]:
        if not file_name.strip():
            raise ValueError("file_name es obligatorio.")

        if not csv_content.strip():
            raise ValueError("csv_content es obligatorio.")

        batch_id = self._create_batch(file_name=file_name.strip())

        try:
            processed_rows, valid_rows, invalid_rows = self._process_rows(
                batch_id=batch_id,
                csv_content=csv_content,
            )
            status = "completed_with_errors" if invalid_rows else "completed"
        except ValueError as error:
            self._record_error(
                batch_id=batch_id,
                row_number=0,
                error_type="schema_error",
                message=str(error),
            )
            processed_rows = 0
            valid_rows = 0
            invalid_rows = 1
            status = "failed"

        self._update_batch(
            batch_id=batch_id,
            processed_rows=processed_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            status=status,
        )

        return {
            "batch": self.get_batch(batch_id),
            "errors": self.get_batch_errors(batch_id),
        }

    def list_items(
        self,
        book_reference: str | None = None,
        condition: str | None = None,
        import_batch_id: str | None = None,
        available_only: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        filters = []
        params: list[Any] = []
        if book_reference:
            filters.append("book_reference = %s")
            params.append(book_reference)
        if condition:
            filters.append("condition = %s")
            params.append(condition)
        if import_batch_id:
            filters.append("import_batch_id = %s")
            params.append(import_batch_id)
        if available_only is True:
            filters.append("quantity_available > 0")

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""
        query = """
        SELECT
            id,
            external_code,
            book_reference,
            quantity_available,
            quantity_reserved,
            condition,
            defects,
            observations,
            import_batch_id
        FROM inventory_items
        {where_clause}
        ORDER BY updated_at DESC, external_code ASC
        LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        query = query.format(where_clause=where_clause)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                items = []
                for row in rows:
                    data = row_to_dict(cursor, row)
                    data["available_flag"] = data.get("quantity_available", 0) > 0
                    items.append(data)
                return items

    def list_batches(self) -> list[dict[str, Any]]:
        query = """
        SELECT
            id,
            file_name,
            upload_date,
            processed_rows,
            valid_rows,
            invalid_rows,
            status
        FROM import_batches
        ORDER BY upload_date DESC
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return [row_to_dict(cursor, row) for row in rows]

    def get_batch(self, batch_id: str) -> dict[str, Any]:
        query = """
        SELECT
            id,
            file_name,
            upload_date,
            processed_rows,
            valid_rows,
            invalid_rows,
            status
        FROM import_batches
        WHERE id = %s
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (batch_id,))
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("El lote solicitado no existe.")
                return row_to_dict(cursor, row)

    def get_batch_errors(self, batch_id: str) -> list[dict[str, Any]]:
        self.get_batch(batch_id)

        query = """
        SELECT
            id,
            batch_id,
            row_number,
            error_type,
            message
        FROM import_errors
        WHERE batch_id = %s
        ORDER BY row_number ASC, id ASC
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (batch_id,))
                rows = cursor.fetchall()
                return [row_to_dict(cursor, row) for row in rows]

    def list_errors(
        self,
        batch_id: str | None = None,
        error_type: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: list[str] = []
        params: list[Any] = []

        if batch_id:
            self.get_batch(batch_id)
            filters.append("errors.batch_id = %s")
            params.append(batch_id)

        if error_type:
            filters.append("errors.error_type = %s")
            params.append(error_type.strip())

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""
        query = f"""
        SELECT
            errors.id,
            errors.batch_id,
            errors.row_number,
            errors.error_type,
            errors.message,
            batches.file_name,
            batches.upload_date,
            batches.status AS batch_status
        FROM import_errors AS errors
        INNER JOIN import_batches AS batches
            ON batches.id = errors.batch_id
        {where_clause}
        ORDER BY batches.upload_date DESC, errors.row_number ASC, errors.id ASC
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [row_to_dict(cursor, row) for row in rows]

    def get_summary(self) -> dict[str, int]:
        inventory_query = """
        SELECT
            COUNT(*) AS total_items,
            COALESCE(SUM(quantity_available), 0) AS total_units_available,
            COALESCE(SUM(quantity_reserved), 0) AS total_units_reserved
        FROM inventory_items
        """

        batch_query = """
        SELECT
            COUNT(*) AS total_batches,
            COALESCE(SUM(CASE WHEN invalid_rows > 0 OR status = 'failed' THEN 1 ELSE 0 END), 0) AS batches_with_errors
        FROM import_batches
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(inventory_query)
                inventory_row = cursor.fetchone()
                cursor.execute(batch_query)
                batch_row = cursor.fetchone()

        return {
            "total_items": int(inventory_row[0]),
            "total_units_available": int(inventory_row[1]),
            "total_units_reserved": int(inventory_row[2]),
            "total_batches": int(batch_row[0]),
            "batches_with_errors": int(batch_row[1]),
        }

    def get_data_quality_summary(self) -> dict[str, Any]:
        batch_query = """
        SELECT
            COUNT(*) AS total_batches,
            COALESCE(SUM(CASE WHEN invalid_rows > 0 OR status = 'failed' THEN 1 ELSE 0 END), 0) AS batches_with_errors,
            COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) AS failed_batches
        FROM import_batches
        """

        total_errors_query = """
        SELECT COUNT(*) AS total_errors
        FROM import_errors
        """

        errors_by_type_query = """
        SELECT
            error_type,
            COUNT(*) AS total
        FROM import_errors
        GROUP BY error_type
        ORDER BY total DESC, error_type ASC
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(batch_query)
                batch_row = cursor.fetchone()
                cursor.execute(total_errors_query)
                total_errors_row = cursor.fetchone()
                cursor.execute(errors_by_type_query)
                error_rows = cursor.fetchall()

        return {
            "total_batches": int(batch_row[0]),
            "batches_with_errors": int(batch_row[1]),
            "failed_batches": int(batch_row[2]),
            "total_errors": int(total_errors_row[0]),
            "errors_by_type": [
                {
                    "error_type": row[0],
                    "total": int(row[1]),
                }
                for row in error_rows
            ],
        }

    def delete_item(self, item_id: str) -> None:
        query = "DELETE FROM inventory_items WHERE id = %s"

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (item_id,))
                deleted = cursor.rowcount
            connection.commit()

        if deleted == 0:
            raise ValueError("El item de inventario solicitado no existe.")

    def delete_batch(self, batch_id: str) -> None:
        self.get_batch(batch_id)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM inventory_items WHERE import_batch_id = %s",
                    (batch_id,),
                )
                cursor.execute("DELETE FROM import_errors WHERE batch_id = %s", (batch_id,))
                cursor.execute("DELETE FROM import_batches WHERE id = %s", (batch_id,))
            connection.commit()

    def _create_batch(self, file_name: str) -> str:
        batch_id = str(uuid.uuid4())
        query = """
        INSERT INTO import_batches (
            id,
            file_name,
            upload_date,
            processed_rows,
            valid_rows,
            invalid_rows,
            status
        ) VALUES (%s, %s, %s, 0, 0, 0, 'processing')
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (batch_id, file_name, utc_now_iso()))
            connection.commit()

        return batch_id

    def _update_batch(
        self,
        batch_id: str,
        processed_rows: int,
        valid_rows: int,
        invalid_rows: int,
        status: str,
    ) -> None:
        query = """
        UPDATE import_batches
        SET processed_rows = %s,
            valid_rows = %s,
            invalid_rows = %s,
            status = %s
        WHERE id = %s
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (processed_rows, valid_rows, invalid_rows, status, batch_id),
                )
            connection.commit()

    def _process_rows(self, batch_id: str, csv_content: str) -> tuple[int, int, int]:
        reader = csv.DictReader(io.StringIO(csv_content))

        if not reader.fieldnames:
            raise ValueError("El CSV debe incluir una fila de encabezados.")

        normalized_headers = {
            self._normalize_header(field_name) for field_name in reader.fieldnames
        }
        missing_columns = REQUIRED_COLUMNS - normalized_headers

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Faltan columnas requeridas: {missing}.")

        processed_rows = 0
        valid_rows = 0
        invalid_rows = 0

        for row_number, raw_row in enumerate(reader, start=2):
            processed_rows += 1
            normalized_row = self._normalize_row(raw_row)

            try:
                valid_item = self._validate_row(normalized_row, row_number)
                self._upsert_inventory_item(batch_id, valid_item)
                valid_rows += 1
            except ValueError as error:
                invalid_rows += 1
                self._record_error(
                    batch_id=batch_id,
                    row_number=row_number,
                    error_type="validation_error",
                    message=str(error),
                )

        return processed_rows, valid_rows, invalid_rows

    def _validate_row(self, row: dict[str, str], row_number: int) -> dict[str, Any]:
        external_code = row.get("external_code", "").strip()
        book_reference = row.get("book_reference", "").strip()
        condition = row.get("condition", "").strip()
        defects = row.get("defects", "").strip()
        observations = row.get("observations", "").strip()

        if not external_code:
            raise ValueError(f"La fila {row_number} no tiene external_code.")

        if not book_reference:
            raise ValueError(f"La fila {row_number} no tiene book_reference.")

        lookup = self.catalog_client.get_book(book_reference)
        if not lookup.reachable:
            raise ValueError(
                f"La fila {row_number} no pudo validarse contra Catalog Service. {lookup.error_message}"
            )
        if not lookup.exists:
            raise ValueError(
                f"La fila {row_number} referencia un libro inexistente en Catalog Service."
            )

        if not condition:
            raise ValueError(f"La fila {row_number} no tiene condition.")

        quantity_available = self._parse_non_negative_int(
            row.get("quantity_available", ""),
            field_name="quantity_available",
            row_number=row_number,
        )
        quantity_reserved = self._parse_non_negative_int(
            row.get("quantity_reserved", ""),
            field_name="quantity_reserved",
            row_number=row_number,
        )

        if quantity_reserved > quantity_available:
            raise ValueError(
                f"La fila {row_number} tiene quantity_reserved mayor que quantity_available."
            )

        self._validate_condition_defects(
            condition=condition,
            defects=defects,
            row_number=row_number,
        )

        return {
            "external_code": external_code,
            "book_reference": book_reference,
            "quantity_available": quantity_available,
            "quantity_reserved": quantity_reserved,
            "condition": condition,
            "defects": defects,
            "observations": observations,
        }

    def _upsert_inventory_item(self, batch_id: str, item: dict[str, Any]) -> None:
        item_id = str(uuid.uuid4())
        query = """
        INSERT INTO inventory_items (
            id,
            external_code,
            book_reference,
            quantity_available,
            quantity_reserved,
            condition,
            defects,
            observations,
            import_batch_id,
            updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(external_code) DO UPDATE SET
            book_reference = excluded.book_reference,
            quantity_available = excluded.quantity_available,
            quantity_reserved = excluded.quantity_reserved,
            condition = excluded.condition,
            defects = excluded.defects,
            observations = excluded.observations,
            import_batch_id = excluded.import_batch_id,
            updated_at = excluded.updated_at
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        item_id,
                        item["external_code"],
                        item["book_reference"],
                        item["quantity_available"],
                        item["quantity_reserved"],
                        item["condition"],
                        item["defects"],
                        item["observations"],
                        batch_id,
                        utc_now_iso(),
                    ),
                )
            connection.commit()

    def _record_error(
        self, batch_id: str, row_number: int, error_type: str, message: str
    ) -> None:
        query = """
        INSERT INTO import_errors (id, batch_id, row_number, error_type, message)
        VALUES (%s, %s, %s, %s, %s)
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (str(uuid.uuid4()), batch_id, row_number, error_type, message),
                )
            connection.commit()

    @staticmethod
    def _normalize_header(value: str | None) -> str:
        return (value or "").strip().lower()

    def _normalize_row(self, row: dict[str | None, str | None]) -> dict[str, str]:
        return {
            self._normalize_header(key): (value or "").strip()
            for key, value in row.items()
            if key is not None
        }

    @staticmethod
    def _parse_non_negative_int(value: str, field_name: str, row_number: int) -> int:
        try:
            parsed = int(str(value).strip())
        except ValueError as error:
            raise ValueError(
                f"La fila {row_number} tiene {field_name} invalido."
            ) from error

        if parsed < 0:
            raise ValueError(
                f"La fila {row_number} tiene {field_name} negativo."
            )

        return parsed

    @staticmethod
    def _condition_requires_defects(condition: str) -> bool:
        normalized = condition.strip().lower()
        if normalized in {"used_fair", "used_poor", "damaged", "defective"}:
            return True
        return "defect" in normalized or "damage" in normalized

    def _validate_condition_defects(
        self,
        condition: str,
        defects: str,
        row_number: int,
    ) -> None:
        if self._condition_requires_defects(condition) and not defects.strip():
            raise ValueError(
                f"La fila {row_number} requiere defects porque la condicion indica defectos."
            )
