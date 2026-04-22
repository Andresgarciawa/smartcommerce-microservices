import os

import httpx
from fastapi import APIRouter, HTTPException

from clients.http_client import ServiceClient
from security import AuthRequired

router = APIRouter(dependencies=[AuthRequired])

catalog_client = ServiceClient(
    base_url=os.getenv("CATALOG_URL", "http://catalog:8000")
)


@router.get("/products")
async def list_products(q: str | None = None, page: int = 1, size: int = 20):
    params = {"q": q, "page": page, "size": size}
    try:
        return await catalog_client.get("/products", params=params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
