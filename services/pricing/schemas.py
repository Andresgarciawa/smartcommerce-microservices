from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detail: str


class PricingCalculateRequest(BaseModel):
    book_reference: str = Field(min_length=1)


class BatchPricingRequest(BaseModel):
    book_references: list[str] = Field(min_length=1)


class PricingReferenceResponse(BaseModel):
    source: str
    external_price: float
    currency: str
    normalized_price: float
    title: str
    buy_link: str | None = None


class PricingDecisionResponse(BaseModel):
    id: str
    book_reference: str
    title: str
    suggested_price: float
    currency: str
    base_price: float
    condition_label: str
    condition_factor: float
    stock_factor: float
    quantity_available_total: int
    reference_count: int
    source_used: str
    external_lookup: dict[str, Any] = Field(default_factory=dict)
    market_references: list[PricingReferenceResponse] = Field(default_factory=list)
    catalog_sync: bool
    explanation: list[str]
    created_at: str


class BatchPricingResponse(BaseModel):
    items: list[PricingDecisionResponse]
    processed: int
    errors: list[dict[str, str]]


class PricingDecisionListResponse(BaseModel):
    items: list[PricingDecisionResponse]
    total: int
