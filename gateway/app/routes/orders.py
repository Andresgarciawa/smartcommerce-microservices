import httpx
from fastapi import APIRouter, HTTPException
from clients.http_client import ServiceClient

router = APIRouter()

orders_client = ServiceClient(base_url="http://orders:8000")


@router.get("/")
async def list_orders(customer_id: str | None = None):
    params = {"customer_id": customer_id} if customer_id else {}
    try:
        return await orders_client.get("/orders", params=params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
