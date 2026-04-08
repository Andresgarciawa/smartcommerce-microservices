from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="Orders Service",
    version="0.1.0",
    description="Servicio base de pedidos (stub).",
)


@app.get("/orders")
def list_orders(customer_id: str | None = None):
    return {
        "items": [],
        "customer_id": customer_id,
        "message": "Orders Service stub",
    }
