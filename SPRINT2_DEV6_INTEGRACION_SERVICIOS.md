# Sprint 2 Dev6 - Integracion entre Servicios

## Objetivo

Cumplir la historia:

> Como sistema, quiero que los microservicios se comuniquen correctamente por API para soportar un flujo distribuido real.

Entregable esperado:

> Integracion real y estable entre microservicios principales.

Este documento resume como quedo implementada la integracion en el repositorio.

## Vista general

La integracion se resolvio en tres niveles:

1. Integracion directa entre microservicios de dominio.
2. Integracion centralizada por `API Gateway / BFF`.
3. Integracion operativa desde frontend hacia los servicios correctos.

## 1. Catalog Service <-> Inventory Service

Esta es la integracion principal que ya existia parcialmente y que sostiene el flujo distribuido real del producto.

### 1.1 Inventory valida contra Catalog

Archivo clave:

- [services/inventory/service.py](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/services/inventory/service.py)
- [services/inventory/catalog_client.py](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/services/inventory/catalog_client.py)

Como funciona:

- Cuando se importa inventario, cada fila trae `book_reference`.
- `InventoryService` llama a `CatalogClient.get_book(book_id)`.
- Ese cliente consulta por HTTP:
  - `GET /api/catalog/books/{book_id}`
- Si el libro no existe en Catalog:
  - la fila se rechaza;
  - se registra un error de validacion;
  - el lote sigue procesando las demas filas.

Resultado:

- Inventory no guarda referencias huerfanas.
- Se mantiene desacoplamiento por API, no por acceso directo a base de datos.

### 1.2 Catalog consulta inventario real

Archivo clave:

- [services/catalog/service.py](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/services/catalog/service.py)
- [services/catalog/inventory_client.py](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/services/catalog/inventory_client.py)

Como funciona:

- Cuando Catalog lista libros o consulta un libro individual:
  - llama por HTTP a Inventory;
  - consume `GET /api/inventory/items`;
  - agrega disponibilidad y reservas al resultado del libro.

Campos enriquecidos en la respuesta de Catalog:

- `quantity_available_total`
- `quantity_reserved_total`
- `inventory_records`
- `inventory_sync`

Resultado:

- Catalog expone una vista comercial enriquecida con datos reales de inventario.
- Si Inventory no responde, Catalog no colapsa: marca `inventory_sync = false`.

## 2. API Gateway / BFF

El PDF tambien habla de consolidar integracion entre dominios. Para eso el gateway era clave, pero tenia contratos desalineados con los servicios reales.

Antes:

- el gateway intentaba consultar endpoints como `/products`;
- no tenia rutas para `inventory`;
- no servia como punto real de entrada para el flujo principal.

Despues:

- se alinearon las rutas del gateway con los endpoints reales de Catalog;
- se agregaron rutas para Inventory;
- se agrego un endpoint de salud agregada para verificar integracion.

### 2.1 Catalog a traves del Gateway

Archivo:

- [gateway/app/routes/catalog.py](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/gateway/app/routes/catalog.py)

Rutas integradas:

- `GET /catalog/summary` -> `GET /api/catalog/summary`
- `GET /catalog/categories` -> `GET /api/catalog/categories`
- `POST /catalog/categories` -> `POST /api/catalog/categories`
- `GET /catalog/categories/{id}` -> `GET /api/catalog/categories/{id}`
- `DELETE /catalog/categories/{id}` -> `DELETE /api/catalog/categories/{id}`
- `GET /catalog/books` -> `GET /api/catalog/books`
- `POST /catalog/books` -> `POST /api/catalog/books`
- `GET /catalog/books/{id}` -> `GET /api/catalog/books/{id}`
- `PUT /catalog/books/{id}` -> `PUT /api/catalog/books/{id}`
- `POST /catalog/books/{id}/publish` -> `POST /api/catalog/books/{id}/publish`
- `POST /catalog/books/{id}/enrich` -> `POST /api/catalog/books/{id}/enrich`
- `DELETE /catalog/books/{id}` -> `DELETE /api/catalog/books/{id}`

### 2.2 Inventory a traves del Gateway

Archivo:

- [gateway/app/routes/inventory.py](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/gateway/app/routes/inventory.py)

Rutas integradas:

- `GET /inventory/summary` -> `GET /api/inventory/summary`
- `GET /inventory/items` -> `GET /api/inventory/items`
- `GET /inventory/batches` -> `GET /api/inventory/batches`
- `GET /inventory/errors` -> `GET /api/inventory/errors`
- `GET /inventory/batches/{id}/errors` -> `GET /api/inventory/batches/{id}/errors`
- `GET /inventory/quality/summary` -> `GET /api/inventory/quality/summary`
- `POST /inventory/imports` -> `POST /api/inventory/imports`
- `DELETE /inventory/items/{id}` -> `DELETE /api/inventory/items/{id}`
- `DELETE /inventory/batches/{id}` -> `DELETE /api/inventory/batches/{id}`

### 2.3 Endpoint de verificacion de integracion

Archivo:

- [gateway/app/routes/integration.py](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/gateway/app/routes/integration.py)

Se agrego:

- `GET /integration/health`

Que valida:

- `catalog`
- `inventory`
- `orders`
- `pricing`
- `auth`

Resultado:

- el sistema puede verificar desde un solo punto si los servicios principales estan arriba;
- si uno falla, el estado general pasa a `degraded`.

## 3. Frontend <-> Servicios

Archivo:

- [src/api/inventory.ts](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/src/api/inventory.ts)
- [src/App.tsx](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/src/App.tsx)

Se corrigio una integracion importante:

Antes:

- el frontend enviaba JSON a `/inventory/imports`;
- pero `Inventory Service` espera `multipart/form-data` con archivo.

Ahora:

- el frontend arma un `FormData`;
- adjunta el CSV como archivo real;
- envia `file` y `file_name` al endpoint correcto.

Resultado:

- el flujo de importacion de inventario ya coincide con el contrato real del backend.

## 4. Docker Compose y descubrimiento entre servicios

Archivo:

- [docker-compose.yml](C:/Users/wgacol/Documents/GitHub/smartcommerce-microservices/docker-compose.yml)

Ajustes realizados:

- el `gateway` ahora depende tambien de `inventory-service`;
- se agrego `INVENTORY_URL=http://inventory-service:8000`;
- se confirmo `CATALOG_URL=http://catalog-service:8001`.

Resultado:

- el gateway conoce las URLs reales de los servicios que consume;
- la topologia docker queda mas coherente con el flujo distribuido del sprint.

## 5. Por que esto cumple el Sprint 2 Dev6

Se cumple porque ya existe comunicacion por API entre servicios principales y no por acoplamiento interno:

- `Inventory -> Catalog` para validar referencias reales.
- `Catalog -> Inventory` para exponer disponibilidad consolidada.
- `Gateway -> Catalog/Inventory/Orders/Pricing/Auth` como punto de entrada unificado.
- `Frontend -> Servicios` usando contratos HTTP correctos.

Ademas, la integracion es mas estable porque:

- los clientes HTTP manejan indisponibilidad de otros servicios;
- el gateway ya apunta a endpoints reales;
- existe un chequeo agregado de salud;
- el flujo de importacion ya respeta el contrato del backend.

## 6. Validacion realizada

Se valido:

- compilacion Python de los archivos modificados con `py_compile`.

No se pudo ejecutar completamente en este entorno:

- pruebas runtime del gateway, porque la `.venv` local no tiene `httpx`;
- build frontend, porque este entorno no tiene `node_modules` instalados.

Eso no cambia la logica de integracion implementada, pero si conviene ejecutar esas validaciones cuando el entorno este completo.

## 7. Siguiente mejora recomendada

Si quieres dejar Dev6 todavia mas fuerte para sustentacion o demo:

- integrar `catalog` de forma automatica con `pricing` y `enrichment`;
- exponer un flujo tipo:
  - enriquecer libro;
  - calcular precio sugerido;
  - publicar libro;
  - consultar disponibilidad consolidada.

Eso cerraria aun mas el objetivo del Sprint 2 de "integracion real entre dominios".
