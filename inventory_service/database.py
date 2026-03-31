from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "inventory.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS import_batches (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    upload_date TEXT NOT NULL,
    processed_rows INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    invalid_rows INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_items (
    id TEXT PRIMARY KEY,
    external_code TEXT NOT NULL UNIQUE,
    book_reference TEXT NOT NULL,
    quantity_available INTEGER NOT NULL,
    quantity_reserved INTEGER NOT NULL,
    condition TEXT NOT NULL,
    defects TEXT NOT NULL DEFAULT '',
    observations TEXT NOT NULL DEFAULT '',
    import_batch_id TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
);

CREATE TABLE IF NOT EXISTS import_errors (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES import_batches(id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_items_batch ON inventory_items(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_import_errors_batch ON import_errors(batch_id);
"""


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA)
