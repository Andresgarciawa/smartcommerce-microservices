from __future__ import annotations

import os
from contextlib import contextmanager


def get_db_config() -> dict[str, str]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "pricing_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }


SCHEMA = """
CREATE TABLE IF NOT EXISTS pricing_decisions (
    id TEXT PRIMARY KEY,
    book_reference TEXT NOT NULL,
    book_title TEXT NOT NULL,
    suggested_price NUMERIC NOT NULL,
    currency TEXT NOT NULL,
    base_price NUMERIC NOT NULL,
    condition_label TEXT NOT NULL,
    condition_factor NUMERIC NOT NULL,
    stock_factor NUMERIC NOT NULL,
    quantity_available_total INTEGER NOT NULL DEFAULT 0,
    reference_count INTEGER NOT NULL DEFAULT 0,
    source_used TEXT NOT NULL,
    external_lookup_json TEXT NOT NULL DEFAULT '{}',
    market_references_json TEXT NOT NULL DEFAULT '[]',
    explanation_json TEXT NOT NULL,
    catalog_sync BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TEXT NOT NULL
);

ALTER TABLE pricing_decisions
    ADD COLUMN IF NOT EXISTS market_references_json TEXT NOT NULL DEFAULT '[]';

ALTER TABLE pricing_decisions
    ADD COLUMN IF NOT EXISTS external_lookup_json TEXT NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_pricing_decisions_book_reference
    ON pricing_decisions(book_reference);

CREATE INDEX IF NOT EXISTS idx_pricing_decisions_created_at
    ON pricing_decisions(created_at DESC);
"""


@contextmanager
def get_connection():
    import psycopg2

    connection = psycopg2.connect(**get_db_config())
    connection.autocommit = False
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA)
        connection.commit()
