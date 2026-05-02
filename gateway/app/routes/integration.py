import os

from fastapi import APIRouter

from clients.http_client import ServiceClient

router = APIRouter()

catalog_client = ServiceClient(
    base_url=os.getenv("CATALOG_URL", "http://catalog-service:8001")
)
inventory_client = ServiceClient(
    base_url=os.getenv("INVENTORY_URL", "http://inventory-service:8000")
)
orders_client = ServiceClient(
    base_url=os.getenv("ORDERS_URL", "http://orders:8000")
)
pricing_client = ServiceClient(
    base_url=os.getenv("PRICING_URL", "http://pricing:8000")
)
auth_client = ServiceClient(
    base_url=os.getenv("AUTH_URL", "http://auth:8000")
)


async def probe_service(name: str, client: ServiceClient, path: str) -> dict[str, str]:
    try:
        await client.get(path)
        return {"service": name, "status": "up"}
    except Exception as error:
        return {"service": name, "status": "down", "detail": str(error)}


@router.get("/health")
async def integration_health():
    services = [
        await probe_service("catalog", catalog_client, "/api/catalog/health"),
        await probe_service("inventory", inventory_client, "/api/inventory/health"),
        await probe_service("orders", orders_client, "/orders"),
        await probe_service("pricing", pricing_client, "/pricing/products?product_ids=healthcheck"),
        await probe_service("auth", auth_client, "/"),
    ]
    overall_status = "ok" if all(service["status"] == "up" for service in services) else "degraded"
    return {
        "status": overall_status,
        "services": services,
    }
