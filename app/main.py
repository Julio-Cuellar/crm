from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.platform.config import settings
from app.platform.db.session import init_db
from app.platform.app_factory import create_app
from app.modules.tenants.interfaces.api.routers.tenants import router as tenants_router
from app.modules.identity.interfaces.api.routers.users import router as users_router
from app.modules.identity.interfaces.api.routers.auth import router as auth_router
from app.modules.catalog.interfaces.api.routers.services import router as services_router
from app.modules.customers.interfaces.api.routers.customers import router as customers_router
from app.modules.reporting.interfaces.api.routers.dashboard import router as dashboard_router
from app.modules.tickets.interfaces.api.routers.tickets import router as tickets_router
from app.modules.conversations.interfaces.api.routers.chats import router as chats_router
from app.legacy.assistant.interfaces.api.routers.bridge import router as bridge_router
from app.modules.conversations.interfaces.api.routers.ws import router as ws_router
from app.modules.scheduling.interfaces.api.routers.appointments import router as appointments_router
from app.platform.messaging.rabbitmq_event_bus import RabbitMQEventBus
from app.modules.identity.infrastructure.messaging.consumers.tenant_created_consumer import TenantCreatedConsumer
from app.modules.identity.infrastructure.messaging.consumers.tenant_projection_consumer import TenantProjectionConsumer
from app.modules.scheduling.infrastructure.messaging.consumers.customer_events_consumer import CustomerEventsConsumer
from app.modules.scheduling.infrastructure.messaging.consumers.service_events_consumer import ServiceEventsConsumer
from app.modules.tickets.infrastructure.messaging.consumers.customer_events_consumer import (
    CustomerEventsConsumer as TicketsCustomerEventsConsumer,
)
from app.modules.conversations.infrastructure.messaging.consumers.customer_events_consumer import (
    CustomerEventsConsumer as ConversationsCustomerEventsConsumer,
)
from app.legacy.assistant.infrastructure.messaging.consumers.chat_inbound_consumer import ChatInboundConsumer
from app.modules.conversations.infrastructure.db.mongo.mongo_client import mongo_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inicializar Base de Datos en modo de desarrollo
    if settings.ENVIRONMENT == "development":
        print("[Lifespan] Inicializando base de datos en modo de desarrollo (Persistencia Activa)...")
        try:
            await init_db(force_drop=False)
        except Exception as e:
            print(f"[Lifespan Error] No se pudo inicializar la base de datos: {e}")
            raise e

    # 1.1. Inicializar MongoDB
    await mongo_client.connect()

    # 2. Inicializar RabbitMQ Event Bus de forma robusta
    print("[Lifespan] Conectando a RabbitMQ...")
    event_bus = RabbitMQEventBus(settings.RABBITMQ_URL)
    consumers = []
    try:
        await event_bus.connect()
        # Inicializar los consumidores asíncronos
        consumers = [
            TenantCreatedConsumer(event_bus.connection),
            TenantProjectionConsumer(event_bus.connection),
            CustomerEventsConsumer(event_bus.connection),
            ServiceEventsConsumer(event_bus.connection),
            TicketsCustomerEventsConsumer(event_bus.connection),
            ConversationsCustomerEventsConsumer(event_bus.connection),
            ChatInboundConsumer(event_bus.connection),
        ]
        for c in consumers:
            await c.start()
    except Exception as e:
        print(f"[Lifespan Warning] No se pudo establecer conexión con RabbitMQ: {e}")
        print("[Lifespan Warning] El backend funcionará de forma degradada (sin publicación ni consumo de eventos).")
        event_bus = None
        consumers = []

    app.state.event_bus = event_bus
    app.state.consumers = consumers

    yield

    # 3. Cerrar conexiones al apagar el servidor
    await mongo_client.disconnect()
    for c in app.state.consumers:
        await c.stop()
    if app.state.event_bus:
        await app.state.event_bus.disconnect()
    print("[Lifespan] Servidor JChat CRM apagado.")


app = create_app(lifespan=lifespan)

# Registro de Routers
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(bridge_router, prefix="/api/v1")
app.include_router(chats_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
app.include_router(appointments_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": "JChat CRM API",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "status": "healthy"
    }
