import os

import httpx
from fastapi import APIRouter, Body, HTTPException

from clients.http_client import ServiceClient
from security import AuthRequired

router = APIRouter(dependencies=[AuthRequired])

pricing_client = ServiceClient(
    base_url=os.getenv("PRICING_URL", "http://pricing:8000")
)


@router.get("/products")
async def get_product_prices(product_ids: str):
    params = {"product_ids": product_ids}
    try:
        return await pricing_client.get("/pricing/products", params=params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.post("/calculate")
async def calculate_price(payload: dict = Body(...)):
    try:
        return await pricing_client.post("/api/pricing/calculate", json=payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.post("/calculate/batch")
async def calculate_prices_batch(payload: dict = Body(...)):
    try:
        return await pricing_client.post("/api/pricing/calculate/batch", json=payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/decisions")
async def list_pricing_decisions(limit: int = 50, offset: int = 0):
    try:
        return await pricing_client.get("/api/pricing/decisions", params={"limit": limit, "offset": offset})
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@router.get("/decisions/{book_reference}")
async def get_pricing_decision(book_reference: str):
    try:
        return await pricing_client.get(f"/api/pricing/decisions/{book_reference}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
