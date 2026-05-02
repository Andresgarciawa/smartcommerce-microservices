# Pricing Audit Hardening

Este documento resume el hardening del flujo de auditoria en `pricing`.

## Topologia RabbitMQ

- Exchange principal: `pricing.audit` (topic)
- Cola principal: `pricing.audit.log`
- Exchange de retry: `pricing.audit.retry` (direct)
- Cola de retry: `pricing.audit.retry.queue` (TTL + redelivery)
- Exchange DLQ: `pricing.audit.dlx` (direct)
- Cola DLQ: `pricing.audit.dlq`

## Flujo

1. `pricing` publica evento en `pricing.audit`.
2. `pricing-audit-worker` consume de `pricing.audit.log`.
3. Si persiste en DB, hace `ACK`.
4. Si falla:
   - Va a retry queue (delay por TTL).
   - Reintenta hasta `PRICING_AUDIT_MAX_RETRIES`.
5. Si supera el maximo, se mueve a DLQ (`pricing.audit.dlq`).

## Variables de configuracion (worker)

- `PRICING_AUDIT_RETRY_DELAY_MS`: retraso entre reintentos (default `5000`)
- `PRICING_AUDIT_MAX_RETRIES`: maximo de intentos antes de DLQ (default `3`)
- `PRICING_AUDIT_RETRY_EXCHANGE`: exchange de retry
- `PRICING_AUDIT_RETRY_QUEUE`: cola de retry
- `PRICING_AUDIT_DLX`: exchange DLQ
- `PRICING_AUDIT_DLQ`: cola DLQ

## Verificacion rapida

1. Generar eventos:
   - `POST /api/pricing/calculate`
2. Ver logs del worker:
   - `docker compose logs pricing-audit-worker --tail=100 -f`
3. Verificar persistencia:
   - `docker compose exec pricing-db psql -U postgres -d pricing_db -c "select event_id,event_type,status,book_reference,occurred_at from pricing_audit_log order by occurred_at desc limit 20;"`
4. Revisar DLQ en RabbitMQ UI:
   - `http://localhost:15672`
   - Cola: `pricing.audit.dlq`
