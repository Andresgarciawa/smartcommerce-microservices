import os

import httpx
from fastapi import APIRouter, HTTPException

from clients.http_client import ServiceClient
from security import AuthRequired

router = APIRouter(dependencies=[AuthRequired])

pricing_client = ServiceClient(
    base_url=os.getenv("PRICING_URL", "http://pricing:8000")
)


@router.get("/products")
async def get_product_prices(product_ids: str):
    # product_ids expected como coma-separado
    params = {"product_ids": product_ids}
    try:
        return await pricing_client.get("/pricing/products", params=params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
