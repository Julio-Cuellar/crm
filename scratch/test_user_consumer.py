import asyncio
import sys
import os
import uuid

# Agrega la carpeta /backend al PATH de búsqueda de Python para poder importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.platform.config import settings
from app.platform.db.session import async_session_factory, init_db
from app.modules.tenants.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.modules.tenants.domain.entities.tenant import Tenant
from app.platform.messaging.rabbitmq_event_bus import RabbitMQEventBus
from app.modules.identity.infrastructure.messaging.consumers.tenant_created_consumer import TenantCreatedConsumer


async def test_user_consumer_flow():
    print("--- INICIANDO PRUEBA DE INTEGRACIÓN: EVENTOS Y MÓDULO DE USUARIOS ---")
    print(f"Postgres URL: {settings.DATABASE_URL}")
    print(f"RabbitMQ URL: {settings.RABBITMQ_URL}")

    # 1. Reiniciar base de datos para asegurar un estado limpio
    print("\n[Paso 1] Inicializando base de datos (Create-Drop)...")
    await init_db()

    # 2. Crear un Tenant de prueba (requerido por la llave foránea en la tabla 'user')
    print("\n[Paso 2] Creando tenant de prueba en base de datos...")
    test_tenant_id = uuid.uuid4()
    async with async_session_factory() as session:
        tenant_repo = SQLAlchemyTenantRepository(session)
        tenant = Tenant(
            id=test_tenant_id,
            name="Consultorio Integración S.A.",
            slug="cons-integ",
            phone_number_id="meta-integ-123",
            timezone="America/Mexico_City",
            locale="es"
        )
        await tenant_repo.save(tenant)
        await session.commit()
    print(f"-> Tenant de prueba guardado con ID: {test_tenant_id}")

    # 3. Inicializar el bus de eventos y el consumidor
    print("\n[Paso 3] Conectando a RabbitMQ e iniciando consumidor...")
    event_bus = RabbitMQEventBus(settings.RABBITMQ_URL)
    await event_bus.connect()

    consumer = TenantCreatedConsumer(event_bus.connection)
    await consumer.start()

    # Esperar un breve instante para asegurar la declaración de colas
    await asyncio.sleep(1)

    # 4. Publicar el evento 'tenant.created'
    print("\n[Paso 4] Publicando evento 'tenant.created'...")
    owner_email = "admin@consinteg.com"
    owner_name = "Dr. Carlos Integración"
    owner_pw_hash = "$2b$12$EjemploDeHashBcryptParaElUsuarioOwnerCarlos123"

    event_payload = {
        "tenantId": str(test_tenant_id),
        "ownerName": owner_name,
        "ownerEmail": owner_email,
        "ownerPasswordHash": owner_pw_hash
    }

    await event_bus.publish("tenant.created", event_payload)
    print("-> Evento publicado exitosamente.")

    # 5. Esperar a que el consumidor procese el mensaje
    print("\n[Paso 5] Esperando 2 segundos para el procesamiento asíncrono del evento...")
    await asyncio.sleep(2)

    # 6. Consultar la base de datos para validar la creación del usuario
    print("\n[Paso 6] Verificando la persistencia del usuario en PostgreSQL...")
    async with async_session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        
        # Buscar usuario por email y tenant
        owner_user = await user_repo.get_by_email_and_tenant(owner_email, test_tenant_id)
        
        if owner_user:
            print("\n=======================================================")
            print("  ¡ÉXITO! EL USUARIO FUE CREADO ASÍNCRONAMENTE:")
            print(f"  ID: {owner_user.id}")
            print(f"  Tenant ID: {owner_user.tenant_id}")
            print(f"  Email: {owner_user.email}")
            print(f"  Nombre: {owner_user.name}")
            print(f"  Rol: {owner_user.role}")
            print(f"  Activo: {owner_user.is_active}")
            print(f"  Hash de Contraseña: {owner_user.password_hash}")
            print("=======================================================")
            
            # Validaciones de integridad
            assert owner_user.tenant_id == test_tenant_id, "El Tenant ID no coincide."
            assert owner_user.email == owner_email, "El email del usuario no coincide."
            assert owner_user.role == "OWNER", "El rol asignado no es OWNER."
            assert owner_user.name == owner_name, "El nombre del usuario no coincide."
            assert owner_user.password_hash == owner_pw_hash, "La contraseña (hash) no coincide."
            print("-> Todas las aserciones pasaron correctamente.")
        else:
            print("\n[ERROR] El usuario no fue encontrado en la base de datos.")
            print("Revisa los logs del consumidor para más detalles.")
            raise RuntimeError("Prueba fallida: El usuario no se persistió en la BD.")

    # 7. Limpieza y apagado
    print("\n[Paso 7] Apagando el consumidor y desconectando del broker...")
    await consumer.stop()
    await event_bus.disconnect()
    print("\n--- PRUEBA DE INTEGRACIÓN FINALIZADA CON ÉXITO ---")


if __name__ == "__main__":
    asyncio.run(test_user_consumer_flow())
