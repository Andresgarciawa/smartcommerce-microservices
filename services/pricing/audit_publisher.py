from __future__ import annotations

import json
import os
from typing import Any

import pika


class AuditPublisher:
    def __init__(self) -> None:
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.exchange = os.getenv("PRICING_AUDIT_EXCHANGE", "pricing.audit")
        self.routing_key = os.getenv("PRICING_AUDIT_ROUTING_KEY", "pricing.decision.event")
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.channel.Channel | None = None

    def connect(self) -> None:
        if self._connection and self._connection.is_open and self._channel and self._channel.is_open:
            return

        params = pika.URLParameters(self.rabbitmq_url)
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()

        self._channel.exchange_declare(
            exchange=self.exchange,
            exchange_type="topic",
            durable=True,
        )

    def publish_event(self, event: dict[str, Any]) -> None:
        self.connect()
        assert self._channel is not None

        body = json.dumps(event, ensure_ascii=True).encode("utf-8")
        self._channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.routing_key,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # persistent
            ),
        )

    def close(self) -> None:
        if self._channel and self._channel.is_open:
            self._channel.close()
        if self._connection and self._connection.is_open:
            self._connection.close()
