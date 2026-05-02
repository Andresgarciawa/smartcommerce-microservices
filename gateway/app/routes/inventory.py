import os

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from clients.http_client import ServiceClient
from security import AuthRequired

router = APIRouter(dependencies=[AuthRequired])

inventory_client = ServiceClient(
    base_url=os.getenv("INVENTORY_URL", "http://inventory-service:8000")
)


@router.get("/summary")
async def get_summary():
    try:
        return await inventory_client.get("/api/inventory/summary")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/items")
async def list_items(
    book_reference: str | None = None,
    condition: str | None = None,
    import_batch_id: str | None = None,
    available_only: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    params = {
        "book_reference": book_reference,
        "condition": condition,
        "import_batch_id": import_batch_id,
        "available_only": available_only,
        "limit": limit,
        "offset": offset,
    }
    filtered_params = {key: value for key, value in params.items() if value is not None}
    try:
        return await inventory_client.get("/api/inventory/items", params=filtered_params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/batches")
async def list_batches():
    try:
        return await inventory_client.get("/api/inventory/batches")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/errors")
async def list_errors(
    batch_id: str | None = None,
    error_type: str | None = None,
):
    params = {
        "batch_id": batch_id,
        "error_type": error_type,
    }
    filtered_params = {key: value for key, value in params.items() if value is not None}
    try:
        return await inventory_client.get("/api/inventory/errors", params=filtered_params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/batches/{batch_id}/errors")
async def get_batch_errors(batch_id: str):
    try:
        return await inventory_client.get(f"/api/inventory/batches/{batch_id}/errors")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/quality/summary")
async def get_quality_summary():
    try:
        return await inventory_client.get("/api/inventory/quality/summary")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.post("/imports")
async def import_inventory(
    file: UploadFile = File(...),
    file_name: str | None = Form(default=None),
):
    files = {
        "file": (
            file_name or file.filename or "inventory.csv",
            await file.read(),
            file.content_type or "text/csv",
        )
    }
    data = {}
    if file_name:
        data["file_name"] = file_name
    try:
        return await inventory_client.post("/api/inventory/imports", files=files, data=data)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    try:
        return await inventory_client.delete(f"/api/inventory/items/{item_id}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.delete("/batches/{batch_id}")
async def delete_batch(batch_id: str):
    try:
        return await inventory_client.delete(f"/api/inventory/batches/{batch_id}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
