# AI Enrichment Service

Microservicio responsable de enriquecer los datos bibliográficos de libros mediante
fuentes externas (Google Books, Open Library, etc.). Forma parte del sistema
**SmartCommerce Microservices**.

> **Sprint 1 — Estado actual:** funcionando en modo **mock** (datos simulados).
> La integración con APIs externas se implementará en sprints posteriores.

---

## Tecnologías

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.13 | Lenguaje principal |
| FastAPI | 0.115.0 | Framework web / API REST |
| Uvicorn | 0.30.6 | Servidor ASGI |
| SQLAlchemy | 2.0.36 | ORM para base de datos |
| PostgreSQL | 15 | Base de datos relacional |
| psycopg2 | 2.9.10 | Driver Python ↔ PostgreSQL |
| Pydantic | 2.9.2 | Validación de datos |
| httpx | 0.27.2 | Cliente HTTP (para APIs externas) |
| Docker | — | Contenedorización |

---

## Estructura del proyecto

```
services/enrichment/
├── Dockerfile                  # Imagen del contenedor
├── requirements.txt            # Dependencias Python
├── README.md                   # Este archivo
└── app/
    ├── main.py                 # Punto de entrada de la aplicación
    ├── domain/
    │   └── models.py           # Modelos Pydantic (contratos de datos)
    ├── infraestructure/
    │   ├── database.py         # Conexión a PostgreSQL
    │   └── orm_models.py       # Modelos ORM (tablas de la BD)
    ├── application/
    │   └── enrich_book.py      # Caso de uso: lógica de enriquecimiento
    └── routers/
        └── enrichment_router.py # Endpoints HTTP
```

---

## Modelo de datos

### Tabla `enrichment_requests`
Registra cada solicitud de enriquecimiento recibida.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (PK) | UUID único de la solicitud |
| `book_reference` | String | ISBN u otro identificador del libro |
| `requested_at` | DateTime | Fecha y hora de la solicitud |
| `source_used` | String | API utilizada para enriquecer |
| `status` | String | `pending` / `success` / `failed` |

### Tabla `enrichment_results`
Almacena el resultado del proceso de enriquecimiento.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (PK) | UUID único del resultado |
| `request_id` | String (FK) | Referencia a `enrichment_requests.id` |
| `normalized_title` | String | Título estandarizado |
| `normalized_author` | String | Autor estandarizado |
| `normalized_publisher` | String | Editorial estandarizada |
| `normalized_description` | Text | Descripción del libro |
| `cover_url` | String | URL de la portada |
| `metadata_json` | JSON | Datos adicionales en formato libre |

---

## Cómo levantar el servicio

### Requisitos previos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo

### Levantar con Docker Compose
Desde la raíz del repositorio (`smartcommerce-microservices/`):

```bash
docker-compose up --build
```

Esto levanta dos contenedores:
- **`enrichment_container`** — El servicio FastAPI (puerto `8005`)
- **`enrichment_db`** — PostgreSQL 15 (puerto `5432`)

Las tablas se crean automáticamente al iniciar el servicio.

### Detener el servicio
```bash
docker-compose down
```

---

## Endpoints disponibles

### `GET /`
Verifica que el servicio está corriendo.

**Response:**
```json
{
  "service": "AI Enrichment Service",
  "status": "online",
  "version": 1
}
```

---

### `POST /enrichment/process`
Procesa una solicitud de enriquecimiento para un libro.

**Request body:**
```json
{
  "book_reference": "978-3-16-148410-0",
  "status": "pending"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `book_reference` | string | ✅ Sí | ISBN u otro identificador del libro |
| `status` | string | No | Estado inicial (default: `"pending"`) |

**Response (200 OK):**
```json
{
  "id": "ee79b55d-a68c-4d37-8b59-6cd7ae173d8a",
  "request_id": "51bd1f2f-8e74-43f4-a32a-5951b085892b",
  "normalized_title": "[Enriched] 978-3-16-148410-0",
  "normalized_author": "Autor Estandarizado (Mock)",
  "normalized_publisher": "Editorial Global (Mock)",
  "normalized_description": "Descripción enriquecida automáticamente.",
  "cover_url": "https://example.com/cover-placeholder.jpg",
  "metadata_json": {
    "source": "mock",
    "enriched_at": "2026-03-29T21:07:50.164474",
    "book_reference": "978-3-16-148410-0"
  }
}
```

---

## Cómo probar

### Opción 1 — Swagger UI (navegador)
Con el servicio corriendo, abre:
```
http://localhost:8005/docs
```
1. Haz clic en `POST /enrichment/process`
2. Clic en **"Try it out"**
3. Edita el body con tu `book_reference`
4. Clic en **"Execute"**

### Opción 2 — Postman
- Método: `POST`
- URL: `http://localhost:8005/enrichment/process`
- Body → raw → JSON:
```json
{
  "book_reference": "978-3-16-148410-0",
  "status": "pending"
}
```

### Opción 3 — cURL
```bash
curl -X POST "http://localhost:8005/enrichment/process" \
  -H "Content-Type: application/json" \
  -d '{"book_reference": "978-3-16-148410-0", "status": "pending"}'
```

> 💡 **Tip:** También puedes importar el schema completo en Postman desde:
> `http://localhost:8005/openapi.json`

---

## Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@db:5432/enrichment_db` | URL de conexión a PostgreSQL |

Se configuran en el `docker-compose.yml` de la raíz del proyecto.

---

## Roadmap

| Sprint | Estado | Descripción |
|---|---|---|
| Sprint 1 | ✅ Completado | Arquitectura base + mock funcional |
| Sprint 2 | 🔲 Pendiente | Integración con Google Books API / Open Library |
| Sprint 3 | 🔲 Pendiente | Persistencia real en BD + manejo de errores |

---

## Desarrollador

**Responsable:** Jorge  
**Microservicio:** AI Enrichment Service  
**Proyecto:** SmartCommerce Microservices — Sistema de Gestión de Biblioteca
