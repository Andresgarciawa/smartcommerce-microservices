from __future__ import annotations

import json
from typing import Any

from .database import get_connection, initialize_database


class AuditRepository:
    def __init__(self) -> None:
        initialize_database()

    def save_event(self, event: dict[str, Any]) -> None:
        query = """
        INSERT INTO pricing_audit_log (
            event_id, correlation_id, event_type, status, service,
            book_reference, decision_id, occurred_at, payload_json, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        event["event_id"],
                        event["correlation_id"],
                        event["event_type"],
                        event["status"],
                        event["service"],
                        event["book_reference"],
                        event.get("decision_id"),
                        event["occurred_at"],
                        json.dumps(event.get("payload", {}), ensure_ascii=True),
                        event["occurred_at"],
                    ),
                )
            connection.commit()

    def list_events(
        self,
        limit: int = 50,
        offset: int = 0,
        book_reference: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        where_parts: list[str] = []
        params: list[Any] = []

        if book_reference:
            where_parts.append("book_reference = %s")
            params.append(book_reference)
        if event_type:
            where_parts.append("event_type = %s")
            params.append(event_type)
        if status:
            where_parts.append("status = %s")
            params.append(status)

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        total_query = f"SELECT COUNT(*) FROM pricing_audit_log {where_clause}"
        data_query = f"""
        SELECT event_id, correlation_id, event_type, status, service, book_reference,
               decision_id, occurred_at, payload_json, created_at
        FROM pricing_audit_log
        {where_clause}
        ORDER BY occurred_at DESC
        LIMIT %s OFFSET %s
        """

        safe_limit = max(1, min(limit, 200))
        safe_offset = max(0, offset)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(total_query, tuple(params))
                total = int(cursor.fetchone()[0])

                cursor.execute(data_query, tuple(params + [safe_limit, safe_offset]))
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

        items: list[dict[str, Any]] = []
        for row in rows:
            item = dict(zip(columns, row))
            item["payload"] = json.loads(item.pop("payload_json") or "{}")
            items.append(item)

        return {"items": items, "total": total}

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        query = """
        SELECT event_id, correlation_id, event_type, status, service, book_reference,
               decision_id, occurred_at, payload_json, created_at
        FROM pricing_audit_log
        WHERE event_id = %s
        LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (event_id,))
                row = cursor.fetchone()
                if row is None:
                    return None
                columns = [desc[0] for desc in cursor.description]

        item = dict(zip(columns, row))
        item["payload"] = json.loads(item.pop("payload_json") or "{}")
        return item
