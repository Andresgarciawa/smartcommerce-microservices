import os

import httpx
from fastapi import APIRouter, Body, HTTPException, Query

from clients.http_client import ServiceClient
from security import AuthRequired

router = APIRouter(dependencies=[AuthRequired])

catalog_client = ServiceClient(
    base_url=os.getenv("CATALOG_URL", "http://catalog-service:8001")
)


@router.get("/summary")
async def get_summary():
    try:
        return await catalog_client.get("/api/catalog/summary")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/categories")
async def list_categories():
    try:
        return await catalog_client.get("/api/catalog/categories")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.post("/categories")
async def create_category(payload: dict = Body(...)):
    try:
        return await catalog_client.post("/api/catalog/categories", json=payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/categories/{category_id}")
async def get_category(category_id: str):
    try:
        return await catalog_client.get(f"/api/catalog/categories/{category_id}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    try:
        return await catalog_client.delete(f"/api/catalog/categories/{category_id}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/books")
async def list_books(
    q: str | None = None,
    category_id: str | None = None,
    published: bool | None = None,
    enriched: bool | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    params = {
        "q": q,
        "category_id": category_id,
        "published": published,
        "enriched": enriched,
        "year_from": year_from,
        "year_to": year_to,
        "limit": limit,
        "offset": offset,
    }
    filtered_params = {key: value for key, value in params.items() if value is not None}
    try:
        return await catalog_client.get("/api/catalog/books", params=filtered_params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.post("/books")
async def create_book(payload: dict = Body(...)):
    try:
        return await catalog_client.post("/api/catalog/books", json=payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/books/{book_id}")
async def get_book(book_id: str):
    try:
        return await catalog_client.get(f"/api/catalog/books/{book_id}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.put("/books/{book_id}")
async def update_book(book_id: str, payload: dict = Body(...)):
    try:
        return await catalog_client.put(f"/api/catalog/books/{book_id}", json=payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.post("/books/{book_id}/publish")
async def publish_book(book_id: str):
    try:
        return await catalog_client.post(f"/api/catalog/books/{book_id}/publish")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.post("/books/{book_id}/enrich")
async def enrich_book(book_id: str, payload: dict = Body(...)):
    try:
        return await catalog_client.post(f"/api/catalog/books/{book_id}/enrich", json=payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.delete("/books/{book_id}")
async def delete_book(book_id: str):
    try:
        return await catalog_client.delete(f"/api/catalog/books/{book_id}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
