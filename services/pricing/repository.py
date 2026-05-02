from __future__ import annotations

import json
from typing import Any

from .database import get_connection, initialize_database


def row_to_dict(cursor, row) -> dict[str, Any]:
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


class PricingRepository:
    def __init__(self) -> None:
        initialize_database()

    def save_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        query = """
        INSERT INTO pricing_decisions (
            id,
            book_reference,
            book_title,
            suggested_price,
            currency,
            base_price,
            condition_label,
            condition_factor,
            stock_factor,
            quantity_available_total,
            reference_count,
            source_used,
            external_lookup_json,
            market_references_json,
            explanation_json,
            catalog_sync,
            created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        decision["id"],
                        decision["book_reference"],
                        decision["title"],
                        decision["suggested_price"],
                        decision["currency"],
                        decision["base_price"],
                        decision["condition_label"],
                        decision["condition_factor"],
                        decision["stock_factor"],
                        decision["quantity_available_total"],
                        decision["reference_count"],
                        decision["source_used"],
                        json.dumps(decision.get("external_lookup", {}), ensure_ascii=True),
                        json.dumps(decision.get("market_references", []), ensure_ascii=True),
                        json.dumps(decision["explanation"], ensure_ascii=True),
                        decision["catalog_sync"],
                        decision["created_at"],
                    ),
                )
            connection.commit()
        return decision

    def get_latest_decision(self, book_reference: str) -> dict[str, Any] | None:
        query = """
        SELECT
            id,
            book_reference,
            book_title AS title,
            suggested_price,
            currency,
            base_price,
            condition_label,
            condition_factor,
            stock_factor,
            quantity_available_total,
            reference_count,
            source_used,
            external_lookup_json,
            market_references_json,
            explanation_json,
            catalog_sync,
            created_at
        FROM pricing_decisions
        WHERE book_reference = %s
        ORDER BY created_at DESC
        LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (book_reference,))
                row = cursor.fetchone()
                if row is None:
                    return None
                data = row_to_dict(cursor, row)
        data["explanation"] = json.loads(data.pop("explanation_json"))
        data["external_lookup"] = json.loads(data.pop("external_lookup_json") or "{}")
        data["market_references"] = json.loads(data.pop("market_references_json") or "[]")
        data["catalog_sync"] = bool(data["catalog_sync"])
        return data

    def list_latest_decisions(self, limit: int, offset: int) -> dict[str, Any]:
        total_query = "SELECT COUNT(DISTINCT book_reference) FROM pricing_decisions"
        query = """
        SELECT DISTINCT ON (book_reference)
            id,
            book_reference,
            book_title AS title,
            suggested_price,
            currency,
            base_price,
            condition_label,
            condition_factor,
            stock_factor,
            quantity_available_total,
            reference_count,
            source_used,
            external_lookup_json,
            market_references_json,
            explanation_json,
            catalog_sync,
            created_at
        FROM pricing_decisions
        ORDER BY book_reference, created_at DESC
        LIMIT %s OFFSET %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(total_query)
                total = int(cursor.fetchone()[0])
                cursor.execute(query, (limit, offset))
                rows = cursor.fetchall()
                items = [row_to_dict(cursor, row) for row in rows]
        for item in items:
            item["explanation"] = json.loads(item.pop("explanation_json"))
            item["external_lookup"] = json.loads(item.pop("external_lookup_json") or "{}")
            item["market_references"] = json.loads(item.pop("market_references_json") or "[]")
            item["catalog_sync"] = bool(item["catalog_sync"])
        return {"items": items, "total": total}
