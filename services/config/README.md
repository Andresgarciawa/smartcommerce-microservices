# Configuration Service - README

## Overview

The Configuration Service (Dev8 - Sprint 1) is a centralized microservice for managing system-wide configuration parameters without requiring code changes.

## Features

- ✅ Centralized configuration management
- ✅ Category-based organization (pricing, inventory, enrichment, system, api)
- ✅ Type validation (string, integer, float, boolean, json, array)
- ✅ Audit trail tracking all changes
- ✅ RESTful API for read/write operations
- ✅ Admin UI for configuration management
- ✅ Default configuration initialization
- ✅ Multi-service consumption support

## Architecture

Following the hexagonal architecture specified in the project:

```
app/
├── routers/           # HTTP endpoints
│   └── configuration.py
├── application/       # Use cases and business logic
│   ├── use_cases.py
│   └── schemas.py
├── domain/           # Pure business logic
│   ├── models.py
│   └── default_config.py
├── infrastructure/   # Database and external services
│   ├── models.py
│   ├── database.py
│   └── repository.py
└── main.py          # FastAPI app entry point
```

## API Endpoints

### Public (Read-only)
- `GET /config/health` - Health check
- `GET /config/` - Get all configurations
- `GET /config/{category}` - Get category configurations
- `GET /config/{category}/{key}` - Get single configuration

### Admin (Write)
- `POST /config/initialize` - Initialize with defaults
- `PUT /config/{category}/{key}` - Update single configuration
- `PUT /config/` - Bulk update configurations
- `GET /config/{category}/{key}/audit` - Get audit log

## Configuration Categories

### 1. Pricing (`pricing.`)
- `condition_factors` - Price multipliers by condition
- `fallback_margin` - Margin when APIs fail
- `reference_sources` - Priority order of price sources
- `outlier_threshold` - Standard deviation threshold
- `min_price` / `max_price` - Price bounds

### 2. Inventory (`inventory.`)
- `max_file_size` - Max upload size (bytes)
- `allowed_formats` - Supported file formats
- `batch_error_threshold` - Max error % threshold
- `required_fields` - Mandatory fields
- `enrichment_batch_size` - Records per batch

### 3. Enrichment (`enrichment.`)
- `priority_sources` - API query order
- `batch_size` - Records per process
- `retry_attempts` - Retry count on failure
- `timeout_ms` - Milliseconds timeout
- `cache_ttl` - Cache time to live

### 4. System (`system.`)
- `jwt_algorithm` - JWT signing algorithm
- `jwt_expiration_hours` - Token expiration
- `external_api_timeout` - API timeout (ms)
- `cache_ttl` - General cache TTL
- `db_pool_size` - Database pool size

### 5. API (`api.`)
- `google_books_enabled` - Enable/disable source
- `crossref_enabled` - Enable/disable source
- `open_library_enabled` - Enable/disable source
- `retry_on_failure` - Retry behavior

## Environment Variables

```bash
# Database
DATABASE_URL_CONFIG=postgresql://user:pass@localhost/config_db
DB_POOL_SIZE=20
DB_POOL_MAX_OVERFLOW=40

# Service
SERVICE_PORT=8008
CORS_ORIGINS=http://localhost:3000

# Logging
SQL_ECHO=false
```

## Usage Examples

### Initialize Configuration
```bash
curl -X POST http://localhost:8008/config/initialize
```

### Get All Configurations
```bash
curl http://localhost:8008/config/
```

### Get Pricing Category
```bash
curl http://localhost:8008/config/pricing
```

### Get Single Configuration
```bash
curl http://localhost:8008/config/pricing/fallback_margin
```

### Update Configuration
```bash
curl -X PUT http://localhost:8008/config/pricing/fallback_margin \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin_token" \
  -d '{"value": 0.20, "reason": "Increase fallback margin"}'
```

### Bulk Update
```bash
curl -X PUT http://localhost:8008/config/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin_token" \
  -d '{
    "updates": {
      "pricing.fallback_margin": 0.20,
      "enrichment.batch_size": 100
    },
    "reason": "Performance optimization"
  }'
```

### Get Audit Log
```bash
curl http://localhost:8008/config/pricing/fallback_margin/audit?limit=50
```

## Database Schema

### configurations table
- `key` (PK): Full parameter key (e.g., "pricing.fallback_margin")
- `value` (JSON): Current value
- `config_type`: Parameter type
- `description`: Human-readable description
- `category`: Category name
- `required`: Whether parameter is required
- `editable`: Whether parameter can be changed
- `updated_at`: Last modification timestamp
- `updated_by`: Admin ID who made change

### configuration_audit_logs table
- `id` (PK): Log entry ID
- `config_key` (FK): Reference to configurations
- `old_value` (JSON): Previous value
- `new_value` (JSON): New value
- `changed_by`: Admin ID
- `change_reason`: Reason for change
- `changed_at`: When change occurred

## Integration with Other Services

Other microservices can consume configuration via:

```python
# Option 1: Direct HTTP call
import requests

response = requests.get(
    "http://config-service:8008/config/pricing"
)
pricing_config = response.json()["parameters"]

# Option 2: Shared client library (recommended)
from config_client import ConfigClient

client = ConfigClient(base_url="http://config-service:8008")
fallback_margin = client.get("pricing.fallback_margin")
```

## Development

### Run Locally
```bash
pip install -r requirements.txt
export DATABASE_URL_CONFIG=postgresql://postgres:postgres@localhost/config_db
uvicorn app.main:app --reload --port 8008
```

### Run Tests
```bash
pytest tests/ -v
```

### Database Migrations
```bash
# Tables are auto-created by SQLAlchemy on first run
# For production, use Alembic for schema management
```

## Next Steps

1. Create Python client library for other services
2. Add Alembic migrations
3. Implement proper JWT validation
4. Add React admin interface
5. Add configuration templates
6. Implement configuration versioning
7. Add configuration rollback capability
8. Add bulk configuration export/import

## Dev8 Checklist

- ✅ Centralized configuration service created
- ✅ Database model and schema defined
- ✅ RESTful API implemented
- ✅ Default configurations loaded
- ✅ Audit trail tracking
- ✅ Type validation
- ✅ Category organization
- ✅ Admin authorization structure
- [ ] React admin UI implementation
- [ ] Integration testing
- [ ] Docker Compose integration
- [ ] Documentation completion

