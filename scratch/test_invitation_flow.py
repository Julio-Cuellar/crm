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
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_invitation_repository import SQLAlchemyInvitationRepository
from app.modules.identity.application.use_cases.register_tenant import RegisterTenantUseCase
from app.modules.identity.application.use_cases.verify_registration import VerifyRegistrationUseCase
from app.modules.tenants.application.use_cases.create_tenant import CreateTenantUseCase
from app.modules.identity.application.use_cases.create_user import CreateUserUseCase
from app.modules.identity.application.use_cases.invite_user import InviteUserUseCase
from app.modules.identity.application.use_cases.get_invitation_by_token import GetInvitationByTokenUseCase
from app.modules.identity.application.use_cases.accept_invitation import AcceptInvitationUseCase
from app.modules.identity.application.use_cases.login import LoginUseCase
from app.platform.messaging.rabbitmq_event_bus import RabbitMQEventBus
from app.modules.identity.infrastructure.messaging.consumers.tenant_created_consumer import TenantCreatedConsumer
from app.platform.security import decode_token


async def test_invitation_flow():
    print("--- INICIANDO PRUEBA DE INTEGRACIÓN: FLUJO DE INVITACIÓN DE COLABORADORES ---")

    # 1. Reiniciar base de datos
    print("\n[Paso 1] Inicializando base de datos...")
    await init_db()

    # 2. Conectar a RabbitMQ y arrancar consumidor
    print("\n[Paso 2] Conectando a RabbitMQ e iniciando consumidor...")
    event_bus = RabbitMQEventBus(settings.RABBITMQ_URL)
    await event_bus.connect()
    
    consumer = TenantCreatedConsumer(event_bus.connection)
    await consumer.start()
    await asyncio.sleep(1)

    # 3. Registrar e inicializar el Tenant (OWNER)
    print("\n[Paso 3] Registrando y verificando al propietario del negocio...")
    owner_email = "owner@dentalcorp.com"
    owner_password = "PasswordOwner123"
    owner_name = "Dr. Alejandro Lopez"
    tenant_name = "Dental Corp Clinic"

    async with async_session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        pending_repo = SQLAlchemyPendingRegistrationRepository(session)
        register_use_case = RegisterTenantUseCase(user_repo, pending_repo, event_bus)
        pending_reg = await register_use_case.execute(
            email=owner_email, password=owner_password, name=owner_name, tenant_name=tenant_name
        )
        await session.commit()
        token_verif = pending_reg.verification_token

    async with async_session_factory() as session:
        pending_repo = SQLAlchemyPendingRegistrationRepository(session)
        tenant_repo = SQLAlchemyTenantRepository(session)
        create_tenant_use_case = CreateTenantUseCase(tenant_repo, event_bus)
        verify_use_case = VerifyRegistrationUseCase(pending_repo, create_tenant_use_case)
        created_tenant = await verify_use_case.execute(email=owner_email, token=token_verif)
        await session.commit()
        tenant_id = created_tenant.id

    # Esperar procesamiento asíncrono para que se cree el OWNER en Postgres
    await asyncio.sleep(2)

    # 4. Enviar Invitación a un colaborador (InviteUserUseCase)
    print("\n[Paso 4] OWNER envía una invitación al colaborador...")
    invited_email = "colaborador@dentalcorp.com"
    invited_role = "STAFF"

    async with async_session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        invitation_repo = SQLAlchemyInvitationRepository(session)
        tenant_repo = SQLAlchemyTenantRepository(session)
        
        invite_use_case = InviteUserUseCase(
            user_repo=user_repo,
            invitation_repo=invitation_repo,
            tenant_repo=tenant_repo,
            event_bus=event_bus
        )
        
        invitation = await invite_use_case.execute(
            tenant_id=tenant_id,
            email=invited_email,
            role=invited_role
        )
        await session.commit()
        invite_token = invitation.token

    print(f"-> Invitación guardada en base de datos. Token generado: {invite_token}")

    # 5. Obtener detalles de la invitación por token (GetInvitationByTokenUseCase)
    print(f"\n[Paso 5] Colaborador consulta token '{invite_token}' antes del formulario...")
    async with async_session_factory() as session:
        invitation_repo = SQLAlchemyInvitationRepository(session)
        tenant_repo = SQLAlchemyTenantRepository(session)
        get_invite_use_case = GetInvitationByTokenUseCase(invitation_repo, tenant_repo)
        
        fetched_invitation, fetched_tenant_name = await get_invite_use_case.execute(invite_token)
        
        print(f"-> Detalles recuperados:")
        print(f"   Email a registrar: {fetched_invitation.email}")
        print(f"   Negocio (Tenant): {fetched_tenant_name}")
        print(f"   Rol pre-configurado: {fetched_invitation.role}")
        assert fetched_invitation.email == invited_email
        assert fetched_tenant_name == tenant_name
        assert fetched_invitation.role == invited_role

    # 6. Aceptar la invitación y rellenar formulario (AcceptInvitationUseCase)
    print("\n[Paso 6] Colaborador completa su registro (nombre y contraseña)...")
    invited_name = "Carlos Empleado"
    invited_password = "PasswordEmpleado123"

    async with async_session_factory() as session:
        invitation_repo = SQLAlchemyInvitationRepository(session)
        user_repo = SQLAlchemyUserRepository(session)
        create_user_use_case = CreateUserUseCase(user_repo)
        
        accept_use_case = AcceptInvitationUseCase(invitation_repo, create_user_use_case)
        
        created_user = await accept_use_case.execute(
            token=invite_token,
            name=invited_name,
            password=invited_password
        )
        await session.commit()

    print(f"-> Registro completado con éxito. Usuario creado:")
    print(f"   ID: {created_user.id}")
    print(f"   Nombre: {created_user.name}")
    print(f"   Email: {created_user.email}")
    print(f"   Rol: {created_user.role}")
    print(f"   Pertenece al Tenant ID: {created_user.tenant_id}")
    
    assert created_user.email == invited_email
    assert created_user.name == invited_name
    assert created_user.role == invited_role
    assert created_user.tenant_id == tenant_id

    # 7. Validar que la invitación haya sido eliminada de la base de datos
    print("\n[Paso 7] Validando que la invitación ya no esté activa...")
    async with async_session_factory() as session:
        invitation_repo = SQLAlchemyInvitationRepository(session)
        deleted_invite = await invitation_repo.get_by_token(invite_token)
        assert deleted_invite is None, "La invitación debió ser eliminada."
    print("-> Confirmado: invitación eliminada correctamente.")

    # 8. Iniciar sesión como el colaborador y validar claims
    print("\n[Paso 8] Iniciando sesión como el nuevo STAFF...")
    async with async_session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        login_use_case = LoginUseCase(user_repo)
        
        user, access_token, refresh_token = await login_use_case.execute(
            email=invited_email,
            password=invited_password
        )
        
    print("-> ¡Login exitoso!")
    claims = decode_token(access_token)
    print("Claims del colaborador en su Access Token:")
    for k, v in claims.items():
        print(f"  {k}: {v}")
        
    assert claims.get("email") == invited_email
    assert claims.get("role") == "STAFF"
    assert claims.get("tenantId") == str(tenant_id)

    # 9. Limpieza y apagado
    print("\n[Paso 9] Apagando el consumidor y cerrando conexiones...")
    await consumer.stop()
    await event_bus.disconnect()
    
    print("\n=========================================================================")
    print("  ¡ÉXITO ABSOLUTO! EL FLUJO COMPLETO DE INVITACIÓN DE COLABORADORES OK  ")
    print("=========================================================================")


if __name__ == "__main__":
    asyncio.run(test_invitation_flow())
