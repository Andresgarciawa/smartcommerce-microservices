from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:
    import psycopg2
except ModuleNotFoundError:  # pragma: no cover - only affects local test envs without postgres driver
    psycopg2 = None


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL,
    publisher TEXT NOT NULL,
    publication_year INTEGER NOT NULL,
    volume TEXT NOT NULL DEFAULT '',
    isbn TEXT NOT NULL DEFAULT '',
    issn TEXT NOT NULL DEFAULT '',
    category_id TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    cover_url TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT '',
    page_count INTEGER NOT NULL DEFAULT 0,
    published_date TEXT NOT NULL DEFAULT '',
    authors_extra TEXT NOT NULL DEFAULT '[]',
    categories_external TEXT NOT NULL DEFAULT '[]',
    thumbnail_url TEXT NOT NULL DEFAULT '',
    source_provider TEXT NOT NULL DEFAULT '',
    source_reference TEXT NOT NULL DEFAULT '',
    enrichment_status TEXT NOT NULL DEFAULT 'pending',
    enrichment_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    last_enriched_at TEXT NOT NULL DEFAULT '',
    suggested_price DOUBLE PRECISION,
    currency TEXT NOT NULL DEFAULT 'COP',
    price_source TEXT NOT NULL DEFAULT '',
    price_updated_at TEXT NOT NULL DEFAULT '',
    enriched_flag BOOLEAN NOT NULL DEFAULT FALSE,
    published_flag BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE INDEX IF NOT EXISTS idx_books_category ON books(category_id);
CREATE INDEX IF NOT EXISTS idx_books_published ON books(published_flag);
"""

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL,
    publisher TEXT NOT NULL,
    publication_year INTEGER NOT NULL,
    volume TEXT NOT NULL DEFAULT '',
    isbn TEXT NOT NULL DEFAULT '',
    issn TEXT NOT NULL DEFAULT '',
    category_id TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    cover_url TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT '',
    page_count INTEGER NOT NULL DEFAULT 0,
    published_date TEXT NOT NULL DEFAULT '',
    authors_extra TEXT NOT NULL DEFAULT '[]',
    categories_external TEXT NOT NULL DEFAULT '[]',
    thumbnail_url TEXT NOT NULL DEFAULT '',
    source_provider TEXT NOT NULL DEFAULT '',
    source_reference TEXT NOT NULL DEFAULT '',
    enrichment_status TEXT NOT NULL DEFAULT 'pending',
    enrichment_score REAL NOT NULL DEFAULT 0,
    last_enriched_at TEXT NOT NULL DEFAULT '',
    suggested_price REAL,
    currency TEXT NOT NULL DEFAULT 'COP',
    price_source TEXT NOT NULL DEFAULT '',
    price_updated_at TEXT NOT NULL DEFAULT '',
    enriched_flag INTEGER NOT NULL DEFAULT 0,
    published_flag INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE INDEX IF NOT EXISTS idx_books_category ON books(category_id);
CREATE INDEX IF NOT EXISTS idx_books_published ON books(published_flag);
"""

POSTGRES_MIGRATIONS = [
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS summary TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS language TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS page_count INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS published_date TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS authors_extra TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS categories_external TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS thumbnail_url TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS source_provider TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS source_reference TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS enrichment_status TEXT NOT NULL DEFAULT 'pending'",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS enrichment_score DOUBLE PRECISION NOT NULL DEFAULT 0",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS last_enriched_at TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS suggested_price DOUBLE PRECISION",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS currency TEXT NOT NULL DEFAULT 'COP'",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS price_source TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS price_updated_at TEXT NOT NULL DEFAULT ''",
    "CREATE INDEX IF NOT EXISTS idx_books_enriched ON books(enriched_flag)",
    "CREATE INDEX IF NOT EXISTS idx_books_enrichment_status ON books(enrichment_status)",
]

SQLITE_MIGRATIONS = [
    "ALTER TABLE books ADD COLUMN summary TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN language TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN page_count INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE books ADD COLUMN published_date TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN authors_extra TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE books ADD COLUMN categories_external TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE books ADD COLUMN thumbnail_url TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN source_provider TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN source_reference TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN enrichment_status TEXT NOT NULL DEFAULT 'pending'",
    "ALTER TABLE books ADD COLUMN enrichment_score REAL NOT NULL DEFAULT 0",
    "ALTER TABLE books ADD COLUMN last_enriched_at TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN suggested_price REAL",
    "ALTER TABLE books ADD COLUMN currency TEXT NOT NULL DEFAULT 'COP'",
    "ALTER TABLE books ADD COLUMN price_source TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN price_updated_at TEXT NOT NULL DEFAULT ''",
    "CREATE INDEX IF NOT EXISTS idx_books_enriched ON books(enriched_flag)",
    "CREATE INDEX IF NOT EXISTS idx_books_enrichment_status ON books(enrichment_status)",
]


class Database:
    def __init__(self, sqlite_path: str | Path | None = None) -> None:
        self.sqlite_path = str(sqlite_path) if sqlite_path else None

    @property
    def is_sqlite(self) -> bool:
        return self.sqlite_path is not None

    def placeholder(self) -> str:
        return "?" if self.is_sqlite else "%s"

    def bool_value(self, value: bool) -> int | bool:
        return int(value) if self.is_sqlite else value

    def row_factory(self, cursor, row) -> dict[str, Any]:
        if isinstance(row, dict):
            return row
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    @contextmanager
    def connection(self) -> Iterator[Any]:
        if self.is_sqlite:
            connection = sqlite3.connect(self.sqlite_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
        else:
            if psycopg2 is None:
                raise RuntimeError("psycopg2 no esta instalado para conexiones PostgreSQL.")
            connection = psycopg2.connect(**get_db_config())
            connection.autocommit = False
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        schema = SQLITE_SCHEMA if self.is_sqlite else POSTGRES_SCHEMA
        with self.connection() as connection:
            cursor = connection.cursor()
            cursor.executescript(schema) if self.is_sqlite else cursor.execute(schema)
            self._apply_migrations(cursor)
            connection.commit()

    def _apply_migrations(self, cursor) -> None:
        migrations = SQLITE_MIGRATIONS if self.is_sqlite else POSTGRES_MIGRATIONS
        for statement in migrations:
            try:
                cursor.execute(statement)
            except Exception as error:
                if self.is_sqlite and "duplicate column name" in str(error).lower():
                    continue
                raise


def get_db_config() -> dict[str, str]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "catalog_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }


def build_database(sqlite_path: str | Path | None = None) -> Database:
    env_path = sqlite_path or os.getenv("CATALOG_SQLITE_PATH")
    return Database(env_path)


@contextmanager
def get_connection(sqlite_path: str | Path | None = None) -> Iterator[Any]:
    database = build_database(sqlite_path)
    with database.connection() as connection:
        yield connection


def initialize_database(sqlite_path: str | Path | None = None) -> None:
    build_database(sqlite_path).initialize()
