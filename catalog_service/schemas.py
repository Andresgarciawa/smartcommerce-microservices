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
    title: str
    subtitle: str = ""
    author: str
    publisher: str
    publication_year: int
    volume: str = ""
    isbn: str
    issn: str
    category_id: str
    description: str = ""
    cover_url: str = ""
    enriched_flag: bool = False
    published_flag: bool = False


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
    quantity_available_total: int
    quantity_reserved_total: int
    inventory_records: int
    inventory_sync: bool


class CatalogSummaryResponse(BaseModel):
    total_categories: int
    total_books: int
    published_books: int
    enriched_books: int
