import httpx
from fastapi import APIRouter, HTTPException

from clients.http_client import ServiceClient

router = APIRouter()

import os


auth_client = ServiceClient(base_url=os.getenv("AUTH_URL", "http://auth:8000"))


@router.post("/verify-2fa")
async def verify_2fa(email: str, code: str):
    params = {"email": email, "code": code}
    try:
        return await auth_client.post("/auth/verify-2fa", params=params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
