from __future__ import annotations

import json
import logging
import os

import pika

from pricing.audit_repository import AuditRepository

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE = os.getenv("PRICING_AUDIT_EXCHANGE", "pricing.audit")
ROUTING_KEY = os.getenv("PRICING_AUDIT_ROUTING_KEY", "pricing.decision.event")
QUEUE = os.getenv("PRICING_AUDIT_QUEUE", "pricing.audit.log")
RETRY_EXCHANGE = os.getenv("PRICING_AUDIT_RETRY_EXCHANGE", "pricing.audit.retry")
RETRY_QUEUE = os.getenv("PRICING_AUDIT_RETRY_QUEUE", "pricing.audit.retry.queue")
RETRY_DELAY_MS = int(os.getenv("PRICING_AUDIT_RETRY_DELAY_MS", "5000"))
DLX = os.getenv("PRICING_AUDIT_DLX", "pricing.audit.dlx")
DLQ = os.getenv("PRICING_AUDIT_DLQ", "pricing.audit.dlq")
MAX_RETRIES = int(os.getenv("PRICING_AUDIT_MAX_RETRIES", "3"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("pricing.audit_worker")


def _get_main_queue_retry_count(properties: pika.BasicProperties) -> int:
    headers = properties.headers or {}
    deaths = headers.get("x-death")
    if not isinstance(deaths, list):
        return 0
    for death in deaths:
        if isinstance(death, dict) and death.get("queue") == QUEUE:
            return int(death.get("count", 0))
    return 0

def main() -> None:
    repo = AuditRepository()
    connection = pika.BlockingConnection(
        pika.URLParameters(RABBITMQ_URL)
    )
    channel = connection.channel()

    # Main exchange for published audit events.
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    # Retry and DLQ exchanges to keep main queue healthy.
    channel.exchange_declare(exchange=RETRY_EXCHANGE, exchange_type="direct", durable=True)
    channel.exchange_declare(exchange=DLX, exchange_type="direct", durable=True)

    channel.queue_declare(
        queue=QUEUE,
        durable=True,
        arguments={"x-dead-letter-exchange": RETRY_EXCHANGE},
    )
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)

    channel.queue_declare(
        queue=RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": RETRY_DELAY_MS,
            "x-dead-letter-exchange": EXCHANGE,
            "x-dead-letter-routing-key": ROUTING_KEY,
        },
    )
    channel.queue_bind(exchange=RETRY_EXCHANGE, queue=RETRY_QUEUE, routing_key=ROUTING_KEY)

    channel.queue_declare(queue=DLQ, durable=True)
    channel.queue_bind(exchange=DLX, queue=DLQ, routing_key=ROUTING_KEY)

    def callback(ch, method, properties, body):
        try:
            event = json.loads(body.decode("utf-8"))
            repo.save_event(event)
            logger.info(
                "audit event persisted event_id=%s type=%s status=%s",
                event.get("event_id"),
                event.get("event_type"),
                event.get("status"),
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as error:
            retries = _get_main_queue_retry_count(properties)
            if retries >= MAX_RETRIES:
                logger.error(
                    "audit event moved to DLQ after retries=%s error=%s",
                    retries,
                    str(error),
                )
                ch.basic_publish(
                    exchange=DLX,
                    routing_key=ROUTING_KEY,
                    body=body,
                    properties=properties,
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            logger.warning(
                "audit event failed, sending to retry queue current_retries=%s error=%s",
                retries,
                str(error),
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=20)
    channel.basic_consume(queue=QUEUE, on_message_callback=callback)
    logger.info(
        "audit_worker listening queue=%s retry_queue=%s dlq=%s max_retries=%s retry_delay_ms=%s",
        QUEUE,
        RETRY_QUEUE,
        DLQ,
        MAX_RETRIES,
        RETRY_DELAY_MS,
    )
    channel.start_consuming()

if __name__ == "__main__":
    main()
