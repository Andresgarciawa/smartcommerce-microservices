from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


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
    isbn: str = ""
    issn: str = ""
    category_id: str
    description: str = ""
    cover_url: str = ""
    summary: str = ""
    language: str = ""
    page_count: int = 0
    published_date: str = ""
    authors_extra: list[str] = Field(default_factory=list)
    categories_external: list[str] = Field(default_factory=list)
    thumbnail_url: str = ""
    source_provider: str = ""
    source_reference: str = ""
    enrichment_status: str = "pending"
    enrichment_score: float = 0
    last_enriched_at: str = ""
    enriched_flag: bool = False
    published_flag: bool = False

    @model_validator(mode="after")
    def validate_identifiers(self) -> "BookCreate":
        if not self.isbn.strip() and not self.issn.strip():
            raise ValueError("Debes enviar al menos uno de estos identificadores: isbn o issn.")
        return self


class BookEnrichmentPayload(BaseModel):
    title: str = ""
    author: str = ""
    publisher: str = ""
    description: str = ""
    cover_url: str = ""
    summary: str = ""
    language: str = ""
    page_count: int = 0
    published_date: str = ""
    authors_extra: list[str] = Field(default_factory=list)
    categories_external: list[str] = Field(default_factory=list)
    thumbnail_url: str = ""
    source_provider: str = ""
    source_reference: str = ""
    enrichment_status: str = "completed"
    enrichment_score: float = 0
    last_enriched_at: str = ""
    enriched_flag: bool = True
    publication_year: int | None = None


class BookUpdate(BaseModel):
    suggested_price: float | None = None
    currency: str | None = None
    price_source: str | None = None
    price_updated_at: str | None = None
    published_flag: bool | None = None


class IntegrationStepResponse(BaseModel):
    step: str
    status: str
    detail: str


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
    summary: str
    language: str
    page_count: int
    published_date: str
    authors_extra: list[str]
    categories_external: list[str]
    thumbnail_url: str
    source_provider: str
    source_reference: str
    enrichment_status: str
    enrichment_score: float
    last_enriched_at: str
    suggested_price: float | None
    currency: str
    price_source: str
    price_updated_at: str
    enriched_flag: bool
    published_flag: bool
    quantity_available_total: int
    quantity_reserved_total: int
    inventory_records: int
    inventory_sync: bool


class BookIntegrationResponse(BaseModel):
    book: BookResponse
    steps: list[IntegrationStepResponse]


class CatalogSummaryResponse(BaseModel):
    total_categories: int
    total_books: int
    published_books: int
    enriched_books: int
