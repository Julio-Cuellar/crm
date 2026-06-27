import json
import uuid
from datetime import datetime, UTC
from typing import Any
import aio_pika
from app.domain.ports.event_bus import EventBus


class RabbitMQEventBus(EventBus):
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.RobustChannel | None = None
        self.exchange: aio_pika.RobustExchange | None = None

    async def connect(self) -> None:
        print("[RabbitMQ] Conectando de forma robusta al broker...")
        self.connection = await aio_pika.connect_robust(self.connection_url)
        self.channel = await self.connection.channel()
        # Declarar exchange de tipo TOPIC y durable
        self.exchange = await self.channel.declare_exchange(
            "jchat.events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        print("[RabbitMQ] Conectado exitosamente al exchange 'jchat.events'.")

    async def disconnect(self) -> None:
        print("[RabbitMQ] Cerrando conexiones...")
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        print("[RabbitMQ] Desconectado.")

    async def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        if not self.channel or not self.exchange:
            raise RuntimeError("El Event Bus no está conectado a RabbitMQ.")

        # Contrato base de evento asíncrono
        message_body = {
            "event_id": str(uuid.uuid4()),
            "event": event_name,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "payload": payload
        }

        message = aio_pika.Message(
            body=json.dumps(message_body).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        # Publicar mensaje utilizando el nombre del evento como routing key
        await self.exchange.publish(message, routing_key=event_name)
        print(f"[RabbitMQ] Evento publicado: '{event_name}'")
        print(f"           Mensaje completo enviado al broker:\n{json.dumps(message_body, indent=2)}")
