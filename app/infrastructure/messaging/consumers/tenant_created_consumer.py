import asyncio
import json
import uuid
import aio_pika
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.application.use_cases.create_user import CreateUserUseCase


class TenantCreatedConsumer:
    def __init__(self, connection: aio_pika.RobustConnection):
        self.connection = connection
        self.channel: aio_pika.RobustChannel | None = None
        self.queue: aio_pika.RobustQueue | None = None
        self.task: asyncio.Task | None = None

    async def start(self) -> None:
        self.channel = await self.connection.channel()
        # Prefetch count para no sobrecargar el worker
        await self.channel.set_qos(prefetch_count=10)

        # Declarar cola durable
        self.queue = await self.channel.declare_queue(
            "users.tenant_created",
            durable=True
        )

        # Enlazar cola al exchange con la routing_key correspondiente
        await self.queue.bind("jchat.events", routing_key="tenant.created")

        # Iniciar loop de consumo en segundo plano
        self.task = asyncio.create_task(self._consume())
        print("[RabbitMQ Consumer] Consumidor 'tenant.created' iniciado y escuchando...")

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.channel:
            await self.channel.close()
        print("[RabbitMQ Consumer] Consumidor 'tenant.created' detenido.")

    async def _consume(self) -> None:
        try:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    # process() asegura que se haga ACK al finalizar el bloque
                    # o NACK con re-queue si ocurre un error no controlado
                    async with message.process():
                        try:
                            event_data = json.loads(message.body.decode("utf-8"))
                            payload = event_data.get("payload", {})

                            tenant_id_str = payload.get("tenantId")
                            owner_name = payload.get("ownerName")
                            owner_email = payload.get("ownerEmail")
                            owner_password_hash = payload.get("ownerPasswordHash")

                            if not all([tenant_id_str, owner_name, owner_email, owner_password_hash]):
                                print(f"[RabbitMQ Consumer] Evento inválido omitido: {payload}")
                                continue

                            tenant_id = uuid.UUID(tenant_id_str)
                            print(f"[RabbitMQ Consumer] Creando OWNER '{owner_email}' para el tenant '{tenant_id}'...")

                            # Reintentos con delay para tolerar lag de commit de la transacción creadora del Tenant
                            max_retries = 5
                            retry_delay = 0.5
                            
                            for attempt in range(1, max_retries + 1):
                                try:
                                    # Abrir sesión explícita de base de datos
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

                                        # Hacer commit físico de la transacción
                                        await session.commit()
                                        print(f"[RabbitMQ Consumer] OWNER '{owner_email}' guardado exitosamente en Postgres.")
                                        break
                                except Exception as e:
                                    if attempt == max_retries:
                                        print(f"[RabbitMQ Consumer] Error crítico tras {max_retries} intentos: {e}")
                                        raise e
                                    print(f"[RabbitMQ Consumer] Intento {attempt} fallido debido a lag de transacción, reintentando en {retry_delay}s... (Error: {e})")
                                    await asyncio.sleep(retry_delay)

                        except Exception as e:
                            print(f"[RabbitMQ Consumer] Error procesando mensaje: {e}")
                            raise e  # Propagar para gatillar NACK
        except asyncio.CancelledError:
            pass
