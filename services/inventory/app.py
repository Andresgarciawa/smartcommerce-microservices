from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    DataQualitySummaryResponse,
    DeleteResponse,
    HealthResponse,
    ImportBatchResponse,
    ImportErrorDetailResponse,
    ImportErrorResponse,
    ImportResponse,
    InventoryItemResponse,
    InventorySummaryResponse,
)
from .service import InventoryService

app = FastAPI(
    title="Inventory Service",
    version="1.0.0",
    description="Microservicio para carga masiva, trazabilidad por lote y consulta de inventario.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = InventoryService()


@app.get("/api/inventory/health", response_model=HealthResponse)
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "inventory"}


@app.get("/api/inventory/summary", response_model=InventorySummaryResponse)
def get_summary() -> dict[str, int]:
    return service.get_summary()


@app.get("/api/inventory/items", response_model=list[InventoryItemResponse])
def list_items(
    book_reference: str | None = None,
    condition: str | None = None,
    import_batch_id: str | None = None,
    available_only: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, object]]:
    return service.list_items(
        book_reference=book_reference,
        condition=condition,
        import_batch_id=import_batch_id,
        available_only=available_only,
        limit=limit,
        offset=offset,
    )


@app.get("/api/inventory/batches", response_model=list[ImportBatchResponse])
def list_batches() -> list[dict[str, object]]:
    return service.list_batches()


@app.get("/api/inventory/errors", response_model=list[ImportErrorDetailResponse])
def list_errors(
    batch_id: str | None = None,
    error_type: str | None = None,
) -> list[dict[str, object]]:
    try:
        return service.list_errors(batch_id=batch_id, error_type=error_type)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get(
    "/api/inventory/batches/{batch_id}/errors",
    response_model=list[ImportErrorResponse],
)
def get_batch_errors(batch_id: str) -> list[dict[str, object]]:
    try:
        return service.get_batch_errors(batch_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post(
    "/api/inventory/imports",
    response_model=ImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_inventory(
    file: UploadFile = File(...),
    file_name: str | None = Form(None),
) -> dict[str, object]:
    try:
        content = await file.read()
        return service.import_file(
            file_name=file_name or file.filename or "",
            file_bytes=content,
            content_type=file.content_type,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get(
    "/api/inventory/quality/summary",
    response_model=DataQualitySummaryResponse,
)
def get_data_quality_summary() -> dict[str, object]:
    return service.get_data_quality_summary()


@app.delete("/api/inventory/items/{item_id}", response_model=DeleteResponse)
def delete_item(item_id: str) -> dict[str, str]:
    try:
        service.delete_item(item_id)
        return {
            "status": "ok",
            "message": "Item de inventario eliminado correctamente.",
        }
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.delete("/api/inventory/batches/{batch_id}", response_model=DeleteResponse)
def delete_batch(batch_id: str) -> dict[str, str]:
    try:
        service.delete_batch(batch_id)
        return {
            "status": "ok",
            "message": "Lote de importacion eliminado correctamente.",
        }
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
