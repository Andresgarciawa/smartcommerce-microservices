from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class DeleteResponse(BaseModel):
    status: str
    message: str


class CategoryCreate(BaseModel):
    name: str
    description: str = ""


class CategoryResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str


class BookCreate(BaseModel):
    id: str | None = None
    title: str
    subtitle: str = ""
    author: str
    publisher: str
    publication_year: int
    volume: str = ""
    isbn: str = ""
    issn: str = ""
    category_id: str
    description: str = ""
    cover_url: str = ""
    enriched_flag: bool = False
    published_flag: bool = False
    suggested_price: float | None = None
    currency: str = "COP"
    price_source: str = ""


class BookUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    author: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    volume: str | None = None
    isbn: str | None = None
    issn: str | None = None
    category_id: str | None = None
    description: str | None = None
    cover_url: str | None = None
    suggested_price: float | None = None
    currency: str | None = None
    price_source: str | None = None


class BookEnrich(BaseModel):
    source: str
    title: str | None = None
    subtitle: str | None = None
    author: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    volume: str | None = None
    isbn: str | None = None
    issn: str | None = None
    category_id: str | None = None
    description: str | None = None
    cover_url: str | None = None
    suggested_price: float | None = None
    currency: str | None = None
    price_source: str | None = None


class BookResponse(BaseModel):
    id: str
    title: str
    subtitle: str
    author: str
    publisher: str
    publication_year: int
    volume: str
    isbn: str
    issn: str
    category_id: str
    category_name: str
    description: str
    cover_url: str
    enriched_flag: bool
    published_flag: bool
    suggested_price: float | None
    currency: str | None
    price_source: str | None
    price_updated_at: str | None
    created_at: str
    updated_at: str
    quantity_available_total: int
    quantity_reserved_total: int
    inventory_records: int
    inventory_sync: bool


class CatalogSummaryResponse(BaseModel):
    total_categories: int
    total_books: int
    published_books: int
    enriched_books: int
