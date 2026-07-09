import uuid
from typing import Any

import aio_pika

from app.platform.db.session import async_session_factory
from app.platform.messaging.consumer_base import RabbitMQConsumer
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.modules.identity.application.use_cases.create_user import CreateUserUseCase


class TenantCreatedConsumer:
    """Crea el usuario OWNER de un tenant al recibir el evento `tenant.created`."""

    def __init__(self, connection: aio_pika.RobustConnection):
        self._consumer = RabbitMQConsumer(
            connection,
            queue_name="users.tenant_created",
            routing_key="tenant.created",
            handler=self._handle,
            label="tenant.created",
        )

    async def start(self) -> None:
        await self._consumer.start()

    async def stop(self) -> None:
        await self._consumer.stop()

    async def _handle(self, event_data: dict[str, Any]) -> None:
        payload = event_data.get("payload", {})
        tenant_id_str = payload.get("tenantId")
        owner_name = payload.get("ownerName")
        owner_email = payload.get("ownerEmail")
        owner_password_hash = payload.get("ownerPasswordHash")

        if not all([tenant_id_str, owner_name, owner_email, owner_password_hash]):
            print(f"[RabbitMQ Consumer] Evento inválido omitido: {payload}")
            return

        tenant_id = uuid.UUID(tenant_id_str)
        print(f"[RabbitMQ Consumer] Creando OWNER '{owner_email}' para el tenant '{tenant_id}'...")

        # Sesión explícita de BD; el reintento por lag de commit lo maneja RabbitMQConsumer.
        async with async_session_factory() as session:
            repo = SQLAlchemyUserRepository(session)
            use_case = CreateUserUseCase(repo)
            await use_case.execute(
                tenant_id=tenant_id,
                email=owner_email,
                password=owner_password_hash,
                name=owner_name,
                role="OWNER",
                is_hashed=True
            )
            await session.commit()
            print(f"[RabbitMQ Consumer] OWNER '{owner_email}' guardado exitosamente en Postgres.")
