from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    DeleteResponse,
    HealthResponse,
    ImportBatchResponse,
    ImportErrorResponse,
    ImportPayload,
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
def list_items() -> list[dict[str, object]]:
    return service.list_items()


@app.get("/api/inventory/batches", response_model=list[ImportBatchResponse])
def list_batches() -> list[dict[str, object]]:
    return service.list_batches()


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
def import_inventory(payload: ImportPayload) -> dict[str, object]:
    try:
        return service.import_csv(
            file_name=payload.file_name,
            csv_content=payload.csv_content,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


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
