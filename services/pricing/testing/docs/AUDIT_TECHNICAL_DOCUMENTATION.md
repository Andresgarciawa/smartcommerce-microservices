# Documentacion Tecnica - Modulo de Auditoria de Pricing

## 1. Resumen

Se implemento un modulo de auditoria para el microservicio `pricing` con arquitectura orientada a eventos usando RabbitMQ.  
El objetivo es registrar trazabilidad de decisiones de precio sin bloquear el flujo principal de calculo.

## 2. Objetivos Tecnicos

- Capturar eventos de auditoria de `pricing` (`started`, `completed`, `failed`).
- Desacoplar la persistencia de auditoria del procesamiento principal.
- Persistir eventos en base de datos para consulta historica.
- Exponer endpoints para consulta de auditoria.
- Incorporar hardening con reintentos y DLQ.

## 3. Arquitectura Implementada

Flujo general:

1. `pricing` calcula precio y publica eventos en RabbitMQ.
2. `pricing-audit-worker` consume eventos desde cola principal.
3. El worker persiste los eventos en tabla `pricing_audit_log`.
4. Si ocurre error, el mensaje pasa por cola de retry.
5. Si supera maximo de reintentos, el mensaje se mueve a DLQ.

Componentes:

- Publicador: `services/pricing/audit_publisher.py`
- Emisor de eventos desde negocio: `services/pricing/service.py`
- Consumidor: `services/pricing/audit_worker.py`
- Persistencia: `services/pricing/audit_repository.py`
- Esquema DB: `services/pricing/database.py`
- API de consulta: `services/pricing/app.py`

## 4. Eventos de Auditoria

### 4.1 Tipos de evento

- `pricing.calculate.started`
- `pricing.calculate.completed`
- `pricing.calculate.failed`

### 4.2 Contrato de evento (JSON)

```json
{
  "event_id": "uuid",
  "correlation_id": "uuid",
  "event_type": "pricing.calculate.started",
  "status": "started|completed|failed",
  "service": "pricing",
  "book_reference": "string",
  "decision_id": "uuid|null",
  "occurred_at": "ISO-8601 UTC",
  "payload": {}
}
```

## 5. Persistencia de Auditoria

Tabla principal: `pricing_audit_log`

Campos:

- `event_id` (PK)
- `correlation_id`
- `event_type`
- `status`
- `service`
- `book_reference`
- `decision_id`
- `occurred_at`
- `payload_json`
- `created_at`

Indices:

- `idx_pricing_audit_book_reference`
- `idx_pricing_audit_correlation_id`
- `idx_pricing_audit_occurred_at`
- `idx_pricing_audit_event_type`

## 6. Endpoints API de Auditoria

Implementados en `services/pricing/app.py`.

### 6.1 Listado de eventos

- `GET /api/pricing/audit`

Query params:

- `limit` (1..200)
- `offset` (>=0)
- `book_reference` (opcional)
- `event_type` (opcional)
- `status` (opcional)

Respuesta:

- `items`: lista de eventos
- `total`: total de eventos segun filtro

### 6.2 Detalle por evento

- `GET /api/pricing/audit/{event_id}`

Retorna un evento individual; `404` si no existe.

## 7. Configuracion de RabbitMQ

Servicio: `rabbitmq:3-management` en `docker-compose.yml`.

Puertos:

- `5672`: AMQP
- `15672`: UI de administracion

Credenciales locales:

- usuario: `admin`
- password: `admin123`

Variables usadas por `pricing`:

- `RABBITMQ_URL`
- `PRICING_AUDIT_EXCHANGE`
- `PRICING_AUDIT_ROUTING_KEY`

Variables usadas por `pricing-audit-worker`:

- `PRICING_AUDIT_QUEUE`
- `PRICING_AUDIT_RETRY_EXCHANGE`
- `PRICING_AUDIT_RETRY_QUEUE`
- `PRICING_AUDIT_RETRY_DELAY_MS`
- `PRICING_AUDIT_DLX`
- `PRICING_AUDIT_DLQ`
- `PRICING_AUDIT_MAX_RETRIES`
- `LOG_LEVEL`

## 8. Hardening Implementado

Se implementaron controles de resiliencia:

- Cola de retry con TTL (reintento diferido).
- DLQ para mensajes fallidos tras maximo de intentos.
- Limite de reintentos configurable.
- Logs operativos del worker:
  - evento persistido
  - evento enviado a retry
  - evento enviado a DLQ

Referencia operativa: `services/pricing/testing/docs/AUDIT_HARDENING.md`.

## 9. Despliegue y Operacion

### 9.1 Build y arranque

```powershell
docker compose build pricing pricing-audit-worker
docker compose up -d pricing pricing-audit-worker rabbitmq pricing-db
```

### 9.2 Verificar worker

```powershell
docker compose logs pricing-audit-worker --tail=100 -f
```

### 9.3 Verificar persistencia

```powershell
docker compose exec pricing-db psql -U postgres -d pricing_db -c "select event_id,event_type,status,book_reference,occurred_at from pricing_audit_log order by occurred_at desc limit 20;"
```

## 10. Troubleshooting Relevante

### Error 406 PRECONDITION_FAILED en RabbitMQ

Motivo: cola ya existente con argumentos distintos (`x-dead-letter-exchange`).

Solucion:

1. Detener worker.
2. Eliminar colas antiguas desde UI RabbitMQ.
3. Levantar worker para recrear colas con configuracion nueva.

## 11. Archivos Modificados/Creados

- `services/pricing/service.py`
- `services/pricing/app.py`
- `services/pricing/schemas.py`
- `services/pricing/database.py`
- `services/pricing/audit_publisher.py`
- `services/pricing/audit_repository.py`
- `services/pricing/audit_worker.py`
- `services/pricing/testing/docs/AUDIT_HARDENING.md`
- `docker-compose.yml`

## 12. Estado de Implementacion

Completado a nivel funcional + hardening base:

- Publicacion de auditoria en RabbitMQ
- Consumo y persistencia en DB
- Consulta via API
- Retry + DLQ + logs

Pendiente opcional:

- Suite de pruebas automaticas para auditoria
- Monitoreo avanzado (metricas/alertas)
- Politicas de retencion/limpieza de auditoria
