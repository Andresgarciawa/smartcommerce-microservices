# Pricing test data kit

Este kit crea data real para probar el microservicio `pricing` en entorno local con `docker-compose`.

## Requisitos

- Servicios arriba: `catalog-service`, `inventory-service`, `pricing`.
- PowerShell.

Puertos por defecto (segun `docker-compose.yml`):
- Catalog: `http://localhost:8004`
- Inventory: `http://localhost:8010`
- Pricing: `http://localhost:8003`

## 1) Sembrar data (catalog + inventory)

```powershell
powershell -ExecutionPolicy Bypass -File services/pricing/testing/testdata/seed_pricing_data.ps1
```

Esto genera:
- Una categoria de prueba.
- 3 libros de prueba.
- Un CSV temporal de inventario con condiciones y stock distintos.
- Importacion del CSV en `inventory`.
- Archivo `services/pricing/testing/testdata/.generated/pricing_seed_output.json` con IDs creados.

## 2) Ejecutar pruebas smoke de pricing

```powershell
powershell -ExecutionPolicy Bypass -File services/pricing/testing/testdata/run_pricing_smoke.ps1
```

Valida:
- `GET /api/pricing/health`
- `POST /api/pricing/calculate` (caso OK)
- `POST /api/pricing/calculate/batch` (mix OK + no existe)
- `GET /api/pricing/decisions`
- `GET /api/pricing/decisions/{book_reference}`
- `GET /pricing/products`
- Caso de error `calculate` con `book_reference` vacio

## 3) Generar payloads con IDs reales

```powershell
powershell -ExecutionPolicy Bypass -File services/pricing/testing/testdata/generate_payloads_from_seed.ps1
```

Este script toma `services/pricing/testing/testdata/.generated/pricing_seed_output.json` y sobrescribe los payloads con IDs reales.

## 4) Payloads listos para Postman/Insomnia

Carpeta: `services/pricing/testing/testdata/payloads`

- `calculate_ok.json`
- `calculate_not_found.json`
- `calculate_bad_request.json`
- `batch_mixed.json`
