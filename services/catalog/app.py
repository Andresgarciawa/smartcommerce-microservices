from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    BookCreate,
    BookEnrichmentPayload,
    BookResponse,
    CatalogSummaryResponse,
    CategoryCreate,
    CategoryResponse,
    DeleteResponse,
    HealthResponse,
)
from .service import CatalogService

app = FastAPI(
    title="Catalog Service",
    version="2.0.0",
    description="Microservicio para registrar y consultar productos bibliograficos enriquecidos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = CatalogService()


@app.get("/api/catalog/health", response_model=HealthResponse)
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "catalog"}


@app.get("/api/catalog/summary", response_model=CatalogSummaryResponse)
def get_summary() -> dict[str, int]:
    return service.get_summary()


@app.get("/api/catalog/categories", response_model=list[CategoryResponse])
def list_categories() -> list[dict[str, object]]:
    return service.list_categories()


@app.post(
    "/api/catalog/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(payload: CategoryCreate) -> dict[str, object]:
    try:
        return service.create_category(payload.name, payload.description)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/catalog/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: str) -> dict[str, object]:
    try:
        return service.get_category(category_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/catalog/books", response_model=list[BookResponse])
def list_books(
    q: str | None = Query(default=None, description="Filtro por titulo, autor o ISBN."),
    category_id: str | None = Query(default=None),
    enriched_only: bool | None = Query(default=None),
    published_only: bool | None = Query(default=None),
) -> list[dict[str, object]]:
    return service.list_books(
        q=q,
        category_id=category_id,
        enriched_only=enriched_only,
        published_only=published_only,
    )


@app.post(
    "/api/catalog/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_book(payload: BookCreate) -> dict[str, object]:
    try:
        return service.create_book(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.patch("/api/catalog/books/{book_id}/enrichment", response_model=BookResponse)
def apply_enrichment(book_id: str, payload: BookEnrichmentPayload) -> dict[str, object]:
    try:
        return service.apply_enrichment(book_id, payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/catalog/books/{book_id}", response_model=BookResponse)
def get_book(book_id: str) -> dict[str, object]:
    try:
        return service.get_book(book_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.delete("/api/catalog/categories/{category_id}", response_model=DeleteResponse)
def delete_category(category_id: str) -> dict[str, str]:
    try:
        service.delete_category(category_id)
        return {"status": "ok", "message": "Categoria eliminada correctamente."}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/catalog/books/{book_id}", response_model=DeleteResponse)
def delete_book(book_id: str) -> dict[str, str]:
    try:
        service.delete_book(book_id)
        return {"status": "ok", "message": "Libro eliminado correctamente."}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
