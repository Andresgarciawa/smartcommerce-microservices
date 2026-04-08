from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="Pricing Service",
    version="0.1.0",
    description="Servicio base de precios (stub).",
)


@app.get("/pricing/products")
def get_product_prices(product_ids: str):
    ids = [item.strip() for item in product_ids.split(",") if item.strip()]
    return {
        "items": [{"product_id": pid, "price": 0.0, "currency": "COP"} for pid in ids],
        "message": "Pricing Service stub",
    }
