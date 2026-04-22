from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg2


def get_db_config() -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "inventory_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }


SCHEMA = """
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
         CREATE INDEX IF NOT EXISTS idx_inventory_items_external_code ON inventory_items(external_code);
         CREATE INDEX IF NOT EXISTS idx_inventory_items_reference ON inventory_items(book_reference);
         CREATE INDEX IF NOT EXISTS idx_import_errors_batch ON import_errors(batch_id);
         """


@contextmanager
def get_connection():
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
