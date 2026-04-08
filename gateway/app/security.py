from __future__ import annotations

import os

import httpx
from fastapi import Depends, Header, HTTPException, status

from clients.http_client import ServiceClient


auth_client = ServiceClient(base_url=os.getenv("AUTH_URL", "http://auth:8000"))


async def validate_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header requerido.",
        )

    try:
        await auth_client.get(
            "/auth/test/private",
            headers={"Authorization": authorization},
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Token invalido o expirado.",
        ) from exc


AuthRequired = Depends(validate_token)
