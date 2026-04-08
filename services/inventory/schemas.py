from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class InventoryItemResponse(BaseModel):
    id: str
    external_code: str
    book_reference: str
    quantity_available: int
    quantity_reserved: int
    condition: str
    defects: str
    observations: str
    import_batch_id: str


class ImportBatchResponse(BaseModel):
    id: str
    file_name: str
    upload_date: str
    processed_rows: int
    valid_rows: int
    invalid_rows: int
    status: str


class ImportErrorResponse(BaseModel):
    id: str
    batch_id: str
    row_number: int
    error_type: str
    message: str


class ImportPayload(BaseModel):
    file_name: str
    csv_content: str


class ImportResponse(BaseModel):
    batch: ImportBatchResponse
    errors: list[ImportErrorResponse]


class InventorySummaryResponse(BaseModel):
    total_items: int
    total_units_available: int
    total_units_reserved: int
    total_batches: int
    batches_with_errors: int


class HealthResponse(BaseModel):
    status: str
    service: str


class DeleteResponse(BaseModel):
    status: str
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detail: str
