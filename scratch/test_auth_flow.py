import asyncio
import sys
import os
import uuid
from datetime import datetime

# Agrega la carpeta /backend al PATH de búsqueda de Python para poder importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.platform.config import settings
from app.platform.db.session import async_session_factory, init_db
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_pending_registration_repository import SQLAlchemyPendingRegistrationRepository
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.modules.tenants.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.modules.identity.application.use_cases.register_tenant import RegisterTenantUseCase
from app.modules.identity.application.use_cases.verify_registration import VerifyRegistrationUseCase
from app.modules.tenants.application.use_cases.create_tenant import CreateTenantUseCase
from app.modules.identity.application.use_cases.login import LoginUseCase
from app.platform.messaging.rabbitmq_event_bus import RabbitMQEventBus
from app.modules.identity.infrastructure.messaging.consumers.tenant_created_consumer import TenantCreatedConsumer
from app.platform.security import decode_token
from app.modules.identity.interfaces.api.dependencies.auth_bearer import get_current_user
from fastapi.security import HTTPAuthorizationCredentials


async def test_auth_and_registration_flow():
    print("--- INICIANDO PRUEBA DE INTEGRACIÓN: FLUJO COMPLETO DE AUTENTICACIÓN ---")

    # 1. Reiniciar la base de datos
    print("\n[Paso 1] Inicializando base de datos limpia...")
    await init_db()

    # 2. Levantar el EventBus y Consumidor
    print("\n[Paso 2] Conectando a RabbitMQ e iniciando consumidor...")
    event_bus = RabbitMQEventBus(settings.RABBITMQ_URL)
    await event_bus.connect()
    
    consumer = TenantCreatedConsumer(event_bus.connection)
    await consumer.start()

    await asyncio.sleep(1)  # Asegura inicio del consumidor

    # 3. Solicitar Registro (RegisterTenantUseCase)
    print("\n[Paso 3] Ejecutando RegisterTenantUseCase (Pre-registro)...")
    email = "owner@dentalsmile.com"
    password = "SuperPassword123"
    name = "Dra. Ana Lopez"
    tenant_name = "Dental Smile Center"

    async with async_session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        pending_repo = SQLAlchemyPendingRegistrationRepository(session)
        
        register_use_case = RegisterTenantUseCase(
            user_repo=user_repo,
            pending_repo=pending_repo,
            event_bus=event_bus
        )
        
        pending_reg = await register_use_case.execute(
            email=email,
            password=password,
            name=name,
            tenant_name=tenant_name
        )
        await session.commit()

    print(f"-> Pre-registro creado. Token temporal: {pending_reg.verification_token}")
    print(f"   Vence el: {pending_reg.token_expires_at}")

    # 4. Obtener y Validar el Token desde la base de datos
    print("\n[Paso 4] Recuperando y verificando token desde la base de datos...")
    async with async_session_factory() as session:
        pending_repo = SQLAlchemyPendingRegistrationRepository(session)
        db_pending = await pending_repo.get_by_email(email)
        assert db_pending is not None, "El registro pendiente no fue encontrado."
        assert db_pending.verification_token == pending_reg.verification_token
        token_to_verify = db_pending.verification_token

    # 5. Verificar Registro (VerifyRegistrationUseCase)
    print(f"\n[Paso 5] Verificando token '{token_to_verify}'...")
    async with async_session_factory() as session:
        pending_repo = SQLAlchemyPendingRegistrationRepository(session)
        tenant_repo = SQLAlchemyTenantRepository(session)
        
        create_tenant_use_case = CreateTenantUseCase(
            tenant_repository=tenant_repo,
            event_bus=event_bus
        )
        verify_use_case = VerifyRegistrationUseCase(
            pending_repo=pending_repo,
            create_tenant_use_case=create_tenant_use_case
        )
        
        created_tenant = await verify_use_case.execute(
            email=email,
            token=token_to_verify
        )
        await session.commit()

    print(f"-> Tenant materializado exitosamente.")
    print(f"   ID: {created_tenant.id}")
    print(f"   Slug generado: {created_tenant.slug}")

    # 6. Esperar a que el consumidor de RabbitMQ asíncrono cree el OWNER en Postgres
    print("\n[Paso 6] Esperando 2 segundos para la creación asíncrona del OWNER...")
    await asyncio.sleep(2)

    # 7. Ejecutar Login (LoginUseCase) y verificar tokens JWT
    print("\n[Paso 7] Ejecutando LoginUseCase con credenciales recién registradas...")
    async with async_session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        login_use_case = LoginUseCase(user_repo=user_repo)
        
        user, access_token, refresh_token = await login_use_case.execute(
            email=email,
            password=password
        )
    
    print("-> ¡Login exitoso!")
    print(f"   Usuario autenticado: {user.name} ({user.email})")
    print(f"   Rol del usuario: {user.role}")
    print(f"   Access Token generado: {access_token[:30]}...")
    print(f"   Refresh Token generado: {refresh_token[:30]}...")

    # 8. Decodificar claims del token
    print("\n[Paso 8] Decodificando claims del Access Token JWT...")
    claims = decode_token(access_token)
    print("Claims decodificados:")
    for k, v in claims.items():
        print(f"  {k}: {v}")
    
    assert claims.get("email") == email
    assert claims.get("role") == "OWNER"
    assert claims.get("tenantId") == str(created_tenant.id)
    assert claims.get("type") == "access"

    # 9. Validar middleware de autenticación (get_current_user)
    print("\n[Paso 9] Probando autenticación mediante get_current_user...")
    async with async_session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        # Simulamos las credenciales enviadas por FastAPI
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token)
        
        current_user = await get_current_user(
            credentials=credentials,
            user_repo=user_repo
        )
        assert current_user.id == user.id
        assert current_user.email == email
        assert current_user.role == "OWNER"
        print(f"-> Éxito: get_current_user resolvió correctamente a '{current_user.name}'")

    # 10. Desconectar y limpiar
    print("\n[Paso 10] Deteniendo consumidor y cerrando conexiones de RabbitMQ...")
    await consumer.stop()
    await event_bus.disconnect()
    
    print("\n=================================================================")
    print("  ¡ÉXITO ABSOLUTO! TODO EL FLUJO DE AUTH E INTEGRACIÓN FUNCIONA")
    print("=================================================================")


if __name__ == "__main__":
    asyncio.run(test_auth_and_registration_flow())
