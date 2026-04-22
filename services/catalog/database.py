from __future__ import annotations
import os
from contextlib import contextmanager
import psycopg2
import psycopg2.extras

def get_db_config() -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "catalog_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }

SCHEMA = """
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
                                              enriched_flag BOOLEAN NOT NULL DEFAULT FALSE,
                                              published_flag BOOLEAN NOT NULL DEFAULT FALSE,
                                              created_at TEXT NOT NULL,
                                              updated_at TEXT NOT NULL,
                                              FOREIGN KEY (category_id) REFERENCES categories(id)
             );

         CREATE INDEX IF NOT EXISTS idx_books_category ON books(category_id);
         CREATE INDEX IF NOT EXISTS idx_books_published ON books(published_flag); \
         """

MIGRATIONS = """
             ALTER TABLE books ADD COLUMN IF NOT EXISTS suggested_price NUMERIC;
             ALTER TABLE books ADD COLUMN IF NOT EXISTS currency TEXT;
             ALTER TABLE books ADD COLUMN IF NOT EXISTS price_source TEXT;
             ALTER TABLE books ADD COLUMN IF NOT EXISTS price_updated_at TEXT;

             CREATE TABLE IF NOT EXISTS book_change_log (
                                                           id TEXT PRIMARY KEY,
                                                           book_id TEXT NOT NULL,
                                                           field_name TEXT NOT NULL,
                                                           old_value TEXT,
                                                           new_value TEXT,
                                                           source TEXT NOT NULL,
                                                           created_at TEXT NOT NULL,
                                                           FOREIGN KEY (book_id) REFERENCES books(id)
             );

             CREATE INDEX IF NOT EXISTS idx_change_log_book ON book_change_log(book_id);
             CREATE INDEX IF NOT EXISTS idx_change_log_created ON book_change_log(created_at);
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
            cursor.execute(MIGRATIONS)
        connection.commit()
