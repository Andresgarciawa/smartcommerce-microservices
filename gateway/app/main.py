from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import catalog, orders, pricing

app = FastAPI(
    title="smartcommerce-gateway",
    version="0.1.0",
    description="BFF / API Gateway para smartcommerce-microservices",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(pricing.router, prefix="/pricing", tags=["pricing"])

@app.get("/health", tags=["health"])
async def health():
    return {"status": "UP"}
