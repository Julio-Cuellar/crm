from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.infrastructure.db.session import init_db
from app.domain.exceptions.base import AppException
from app.interfaces.api.routers.tenants import router as tenants_router
from app.interfaces.api.routers.users import router as users_router
from app.interfaces.api.routers.auth import router as auth_router
from app.interfaces.api.routers.services import router as services_router
from app.interfaces.api.routers.customers import router as customers_router
from app.interfaces.api.routers.dashboard import router as dashboard_router
from app.interfaces.api.routers.tickets import router as tickets_router
from app.interfaces.api.routers.chats import router as chats_router
from app.interfaces.api.routers.bridge import router as bridge_router
from app.interfaces.api.routers.ws import router as ws_router
from app.interfaces.api.routers.appointments import router as appointments_router
from app.infrastructure.messaging.rabbitmq_event_bus import RabbitMQEventBus
from app.infrastructure.messaging.consumers.tenant_created_consumer import TenantCreatedConsumer
from app.infrastructure.db.mongo.mongo_client import mongo_client


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
    consumer = None
    try:
        await event_bus.connect()
        # Inicializar el consumidor asíncrono
        consumer = TenantCreatedConsumer(event_bus.connection)
        await consumer.start()
    except Exception as e:
        print(f"[Lifespan Warning] No se pudo establecer conexión con RabbitMQ: {e}")
        print("[Lifespan Warning] El backend funcionará de forma degradada (sin publicación ni consumo de eventos).")
        event_bus = None
        consumer = None
        
    app.state.event_bus = event_bus
    app.state.tenant_created_consumer = consumer

    yield

    # 3. Cerrar conexiones al apagar el servidor
    await mongo_client.disconnect()
    if app.state.tenant_created_consumer:
        await app.state.tenant_created_consumer.stop()
    if app.state.event_bus:
        await app.state.event_bus.disconnect()
    print("[Lifespan] Servidor JChat CRM apagado.")


app = FastAPI(
    title="JChat CRM API",
    description="Backend Multi-Tenant para automatización de citas y mensajería en canales de Meta.",
    version="0.1.0",
    lifespan=lifespan
)

# Configuración básica de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se debe restringir a los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler global para excepciones del dominio
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.message}}
    )


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
