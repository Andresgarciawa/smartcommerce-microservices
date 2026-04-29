from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    BatchPricingRequest,
    BatchPricingResponse,
    ErrorResponse,
    HealthResponse,
    PricingCalculateRequest,
    PricingDecisionListResponse,
    PricingDecisionResponse,
)
from .service import PricingService

app = FastAPI(
    title="Pricing Service",
    version="1.0.0",
    description="Microservicio para calcular precios sugeridos trazables y explicables.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = PricingService()


@app.get("/api/pricing/health", response_model=HealthResponse)
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "pricing"}


@app.post(
    "/api/pricing/calculate",
    response_model=PricingDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def calculate_price(payload: PricingCalculateRequest) -> dict[str, object]:
    try:
        return service.calculate_price(payload.book_reference)
    except ValueError as error:
        message = str(error)
        status_code = 404 if "no existe" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post(
    "/api/pricing/calculate/batch",
    response_model=BatchPricingResponse,
    status_code=status.HTTP_201_CREATED,
)
def calculate_prices_batch(payload: BatchPricingRequest) -> dict[str, object]:
    return service.calculate_prices_batch(payload.book_references)


@app.get("/api/pricing/decisions", response_model=PricingDecisionListResponse)
def list_pricing_decisions(limit: int = 50, offset: int = 0) -> dict[str, object]:
    return service.list_pricing_decisions(limit=limit, offset=offset)


@app.get(
    "/api/pricing/decisions/{book_reference}",
    response_model=PricingDecisionResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_latest_decision(book_reference: str) -> dict[str, object]:
    try:
        return service.get_latest_decision(book_reference)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/pricing/products")
def get_product_prices(product_ids: str) -> dict[str, object]:
    book_references = [item.strip() for item in product_ids.split(",") if item.strip()]
    return service.get_legacy_product_prices(book_references)
