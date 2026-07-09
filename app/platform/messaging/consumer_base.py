import asyncio
import json
from typing import Any, Awaitable, Callable

import aio_pika

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class RabbitMQConsumer:
    """Base reusable para consumidores de eventos de dominio sobre `jchat.events`.

    Declara una cola durable enlazada a una routing key, y por cada mensaje
    decodifica el sobre JSON y llama a `handler(event_data)` dentro de un
    `message.process()` (ack automático al salir sin excepción; nack+requeue
    si el handler termina lanzando tras agotar los reintentos). Este es el
    mismo patrón que usaba `TenantCreatedConsumer` antes de factorizarse aquí
    (declare/bind/qos + reintentos con delay fijo para tolerar lag de commit
    de la transacción publicadora).
    """

    def __init__(
        self,
        connection: aio_pika.RobustConnection,
        *,
        queue_name: str,
        routing_key: str | list[str],
        handler: EventHandler,
        exchange_name: str = "jchat.events",
        prefetch_count: int = 10,
        max_retries: int = 5,
        retry_delay: float = 0.5,
        label: str | None = None,
    ) -> None:
        self.connection = connection
        self.queue_name = queue_name
        self.routing_keys = [routing_key] if isinstance(routing_key, str) else routing_key
        self.handler = handler
        self.exchange_name = exchange_name
        self.prefetch_count = prefetch_count
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.label = label or queue_name
        self.channel: aio_pika.RobustChannel | None = None
        self.queue: aio_pika.RobustQueue | None = None
        self.task: asyncio.Task | None = None

    async def start(self) -> None:
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.prefetch_count)
        self.queue = await self.channel.declare_queue(self.queue_name, durable=True)
        for routing_key in self.routing_keys:
            await self.queue.bind(self.exchange_name, routing_key=routing_key)
        self.task = asyncio.create_task(self._consume())
        print(f"[RabbitMQ Consumer] Consumidor '{self.label}' iniciado y escuchando...")

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.channel:
            await self.channel.close()
        print(f"[RabbitMQ Consumer] Consumidor '{self.label}' detenido.")

    async def _consume(self) -> None:
        try:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        await self._handle_with_retry(message)
        except asyncio.CancelledError:
            pass

    async def _handle_with_retry(self, message: aio_pika.IncomingMessage) -> None:
        try:
            event_data = json.loads(message.body.decode("utf-8"))
        except Exception as e:
            print(f"[RabbitMQ Consumer:{self.label}] Mensaje no es JSON válido, se descarta: {e}")
            return

        for attempt in range(1, self.max_retries + 1):
            try:
                await self.handler(event_data)
                return
            except Exception as e:
                if attempt == self.max_retries:
                    print(f"[RabbitMQ Consumer:{self.label}] Error crítico tras {self.max_retries} intentos: {e}")
                    raise
                print(
                    f"[RabbitMQ Consumer:{self.label}] Intento {attempt} fallido "
                    f"(reintentando en {self.retry_delay}s...): {e}"
                )
                await asyncio.sleep(self.retry_delay)
