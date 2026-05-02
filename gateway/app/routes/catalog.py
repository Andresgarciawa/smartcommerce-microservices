import os

import httpx
from fastapi import APIRouter, Body, HTTPException

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
    published_only: bool | None = None,
    enriched_only: bool | None = None,
):
    params = {
        "q": q,
        "category_id": category_id,
        "published_only": published_only,
        "enriched_only": enriched_only,
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


@router.patch("/books/{book_id}/enrichment")
async def enrich_book(book_id: str, payload: dict = Body(...)):
    try:
        return await catalog_client._request(
            "PATCH",
            f"/api/catalog/books/{book_id}/enrichment",
            json=payload,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.post("/books/{book_id}/integrate")
async def integrate_book(book_id: str):
    try:
        return await catalog_client.post(f"/api/catalog/books/{book_id}/integrate")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.delete("/books/{book_id}")
async def delete_book(book_id: str):
    try:
        return await catalog_client.delete(f"/api/catalog/books/{book_id}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
