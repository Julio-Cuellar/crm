import asyncio
import json
import sys
import os
import urllib.request
import urllib.error

# Agrega la carpeta /backend al PATH de búsqueda de Python para poder importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.db.session import async_session_factory, init_db
from app.infrastructure.db.repositories.sqlalchemy_pending_registration_repository import SQLAlchemyPendingRegistrationRepository
from app.infrastructure.db.repositories.sqlalchemy_invitation_repository import SQLAlchemyInvitationRepository

API_BASE = "http://127.0.0.1:8000/api/v1"


def make_request(url, data=None, method="GET", headers=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
            
    if data:
        json_data = json.dumps(data).encode("utf-8")
        req.data = json_data
        
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            return status_code, json.loads(body)
    except urllib.error.HTTPError as e:
        status_code = e.code
        body = e.read().decode("utf-8")
        try:
            return status_code, json.loads(body)
        except json.JSONDecodeError:
            return status_code, body
    except Exception as e:
        return 0, str(e)


async def get_verification_token(email: str) -> str | None:
    for _ in range(15):
        async with async_session_factory() as session:
            repo = SQLAlchemyPendingRegistrationRepository(session)
            pending = await repo.get_by_email(email)
            if pending and pending.verification_token:
                return pending.verification_token
        await asyncio.sleep(0.2)
    return None


async def get_invitation_token_direct(email: str) -> str | None:
    for _ in range(15):
        async with async_session_factory() as session:
            from app.infrastructure.db.models.invitation import Invitation as DbInvitation
            from sqlalchemy import select
            stmt = select(DbInvitation).where(DbInvitation.email == email)
            result = await session.execute(stmt)
            db_invite = result.scalar_one_or_none()
            if db_invite and db_invite.token:
                return db_invite.token
        await asyncio.sleep(0.2)
    return None


async def run_complete_flow_test():
    print("=========================================================================")
    print("      INICIANDO PRUEBA DEL FLUJO COMPLETO E2E (REST API & DB) ")
    print("=========================================================================")
    
    # 1. Reiniciar la base de datos para asegurar una prueba limpia y aislada
    print("\n[Paso 1] Reiniciando base de datos Postgres (Clean State)...")
    await init_db(force_drop=True)
    print("-> Base de datos limpia.")

    # Datos de prueba para el Tenant y el Propietario (OWNER)
    owner_email = "alejandro.gomez@dentalsanjose.com"
    owner_password = "PasswordSeguroOwner123"
    owner_name = "Dr. Alejandro Gomez"
    tenant_name = "Consultorio Dental San Jose E2E"

    # 2. POST /auth/register - Registrar Tenant (Pre-registro)
    print("\n[Paso 2] Registrando Tenant a través de /auth/register...")
    register_payload = {
        "email": owner_email,
        "password": owner_password,
        "name": owner_name,
        "tenantName": tenant_name
    }
    status, response = make_request(f"{API_BASE}/auth/register", data=register_payload, method="POST")
    print(f"-> Respuesta (HTTP {status}): {response.get('message')}")
    assert status == 202, "El pre-registro debió retornar HTTP 202."

    # 3. Obtener el código de verificación desde Postgres
    print("\n[Paso 3] Obteniendo código de verificación desde la base de datos...")
    verif_token = await get_verification_token(owner_email)
    print(f"-> Código de verificación temporal obtenido: {verif_token}")
    assert verif_token is not None, "El token de verificación no debe ser nulo."

    # 4. POST /auth/verify - Verificar código y concretar creación del Tenant
    print(f"\n[Paso 4] Verificando código '{verif_token}' en /auth/verify...")
    verify_payload = {
        "email": owner_email,
        "token": verif_token
    }
    status, response = make_request(f"{API_BASE}/auth/verify", data=verify_payload, method="POST")
    print(f"-> Respuesta (HTTP {status}):")
    print(json.dumps(response, indent=2))
    assert status == 201, "La verificación debió retornar HTTP 201 Created."
    tenant_id = response.get("id")

    # Esperar 2 segundos para dar tiempo al broker RabbitMQ de crear el OWNER
    print("\nEsperando 2 segundos para la creación asíncrona del usuario OWNER en Postgres...")
    await asyncio.sleep(2)

    # 5. POST /auth/login - Iniciar sesión como el OWNER
    print("\n[Paso 5] Iniciando sesión como OWNER en /auth/login...")
    owner_login_payload = {
        "email": owner_email,
        "password": owner_password
    }
    status, response = make_request(f"{API_BASE}/auth/login", data=owner_login_payload, method="POST")
    print(f"-> Respuesta (HTTP {status}): Login Exitoso.")
    assert status == 200, "El login debió retornar HTTP 200."
    owner_access_token = response.get("accessToken")
    owner_headers = {"Authorization": f"Bearer {owner_access_token}"}

    # 6. GET /auth/me - Verificar perfil del OWNER
    print("\n[Paso 6] Consultando perfil protegido de OWNER en /auth/me...")
    status, response = make_request(f"{API_BASE}/auth/me", method="GET", headers=owner_headers)
    print(f"-> Perfil obtenido (HTTP {status}):")
    print(f"   Nombre: {response.get('name')}")
    print(f"   Email: {response.get('email')}")
    print(f"   Rol: {response.get('role')}")
    print(f"   Tenant ID: {response.get('tenantId')}")
    assert status == 200
    assert response.get("role") == "OWNER"

    # Datos de prueba para el Colaborador (STAFF)
    staff_email = "asistente.carlos@dentalsanjose.com"
    staff_role = "STAFF"

    # 7. POST /users/invite - OWNER invita a colaborador (STAFF)
    print(f"\n[Paso 7] OWNER invita a colaborador '{staff_email}' con rol '{staff_role}'...")
    invite_payload = {
        "email": staff_email,
        "role": staff_role
    }
    status, response = make_request(f"{API_BASE}/users/invite", data=invite_payload, method="POST", headers=owner_headers)
    print(f"-> Respuesta (HTTP {status}): Invitación creada con éxito.")
    assert status == 201, "La creación de invitación debió retornar HTTP 201."

    # 8. Obtener el token de invitación de la base de datos
    print("\n[Paso 8] Obteniendo token de invitación desde Postgres...")
    invite_token = await get_invitation_token_direct(staff_email)
    print(f"-> Token de invitación temporal obtenido: {invite_token}")
    assert invite_token is not None, "El token de invitación no debe ser nulo."

    # 9. GET /auth/invitations/{token} - Colaborador consulta detalles de la invitación
    print(f"\n[Paso 9] Colaborador consulta detalles de la invitación /auth/invitations/{invite_token}...")
    status, response = make_request(f"{API_BASE}/auth/invitations/{invite_token}", method="GET")
    print(f"-> Detalles obtenidos (HTTP {status}):")
    print(f"   Email invitado: {response.get('email')}")
    print(f"   Negocio a unirse: {response.get('tenantName')}")
    print(f"   Rol asignado: {response.get('role')}")
    assert status == 200
    assert response.get("email") == staff_email
    assert response.get("tenantName") == tenant_name

    # 10. POST /auth/invitations/accept - Colaborador completa registro
    print("\n[Paso 10] Colaborador completa registro a través de /auth/invitations/accept...")
    staff_name = "Carlos Asistente"
    staff_password = "PasswordStaff123"
    accept_payload = {
        "token": invite_token,
        "name": staff_name,
        "password": staff_password
    }
    status, response = make_request(f"{API_BASE}/auth/invitations/accept", data=accept_payload, method="POST")
    print(f"-> Respuesta (HTTP {status}): Colaborador registrado correctamente.")
    assert status == 201

    # 11. POST /auth/login - Iniciar sesión como el nuevo STAFF
    print("\n[Paso 11] Iniciando sesión como el nuevo STAFF en /auth/login...")
    staff_login_payload = {
        "email": staff_email,
        "password": staff_password
    }
    status, response = make_request(f"{API_BASE}/auth/login", data=staff_login_payload, method="POST")
    print(f"-> Respuesta (HTTP {status}): Login Exitoso.")
    assert status == 200
    staff_access_token = response.get("accessToken")
    staff_headers = {"Authorization": f"Bearer {staff_access_token}"}

    # 12. GET /auth/me - Verificar perfil del STAFF
    print("\n[Paso 12] Consultando perfil protegido de STAFF en /auth/me...")
    status, response = make_request(f"{API_BASE}/auth/me", method="GET", headers=staff_headers)
    print(f"-> Perfil obtenido (HTTP {status}):")
    print(f"   Nombre: {response.get('name')}")
    print(f"   Email: {response.get('email')}")
    print(f"   Rol: {response.get('role')}")
    print(f"   Tenant ID: {response.get('tenantId')}")
    assert status == 200
    assert response.get("role") == "STAFF"
    assert response.get("tenantId") == tenant_id

    # 13. GET /users/ - Listar usuarios como STAFF (para verificar pertenencia de ambos)
    print("\n[Paso 13] Listando usuarios del tenant como STAFF...")
    status, response = make_request(f"{API_BASE}/users/", method="GET", headers=staff_headers)
    print(f"-> Lista de usuarios (HTTP {status}):")
    for u in response:
        print(f"   - {u.get('name')} ({u.get('email')}) - Rol: {u.get('role')}")
    assert status == 200
    assert len(response) == 2, "Deben haber exactamente 2 usuarios (OWNER y STAFF) en el tenant."

    # 15. Configurar WhatsApp (GET/PUT)
    print("\n[Paso 15] Probando configuración de canal de WhatsApp (GET/PUT)...")
    # GET inicial
    status, config = make_request(f"{API_BASE}/tenants/me/whatsapp", method="GET", headers=owner_headers)
    print(f"-> Configuración de WhatsApp inicial (HTTP {status}): {config}")
    assert status == 200
    
    # PUT para guardar configuración
    whatsapp_payload = {
        "phoneNumberId": "123456789012345",
        "whatsappApiToken": "EAAGkb4L2p98BA...secret_token_here..."
    }
    status, config = make_request(f"{API_BASE}/tenants/me/whatsapp", data=whatsapp_payload, method="PUT", headers=owner_headers)
    print(f"-> Configuración de WhatsApp actualizada (HTTP {status}): {config}")
    assert status == 200
    assert config.get("phoneNumberId") == "123456789012345"
    assert config.get("whatsappApiToken") == "EAAGkb4L2p98BA...secret_token_here..."

    # GET para verificar persistencia y desencripción
    status, config = make_request(f"{API_BASE}/tenants/me/whatsapp", method="GET", headers=owner_headers)
    print(f"-> Configuración de WhatsApp verificada (HTTP {status}): {config}")
    assert status == 200
    assert config.get("phoneNumberId") == "123456789012345"
    assert config.get("whatsappApiToken") == "EAAGkb4L2p98BA...secret_token_here..."

    # 16. Crear cliente y probar flujos de chat/mensajes (MongoDB + Postgres)
    print("\n[Paso 16] Probando flujos de chat e historial de mensajes (Postgres + MongoDB)...")
    # Crear cliente para chatear
    customer_payload = {
        "name": "Julio Cortazar E2E",
        "phone": "+5491122334455",
        "email": "julio.e2e@cortazar.com"
    }
    status, customer = make_request(f"{API_BASE}/customers/", data=customer_payload, method="POST", headers=owner_headers)
    print(f"-> Cliente creado (HTTP {status}): {customer}")
    assert status == 201
    customer_id = customer.get("id")
    assert customer_id is not None

    # Enviar mensaje de chat
    msg_payload = {
        "content": "Hola Julio, este es un mensaje automatizado desde la prueba E2E."
    }
    status, message = make_request(f"{API_BASE}/chats/{customer_id}/messages", data=msg_payload, method="POST", headers=owner_headers)
    print(f"-> Mensaje enviado y guardado (HTTP {status}): {message}")
    assert status == 201
    assert message.get("content") == msg_payload["content"]
    assert message.get("direction") == "OUTBOUND"
    
    # Listar chats activos del tenant
    status, chats = make_request(f"{API_BASE}/chats", method="GET", headers=owner_headers)
    print(f"-> Lista de chats del tenant (HTTP {status}): {chats}")
    assert status == 200
    assert len(chats) > 0
    assert chats[0].get("customerName") == "Julio Cortazar E2E"
    
    # Obtener historial de mensajes de la conversación
    status, history = make_request(f"{API_BASE}/chats/{customer_id}/messages", method="GET", headers=owner_headers)
    print(f"-> Historial de mensajes del chat (HTTP {status}): {history}")
    assert status == 200
    assert len(history) > 0
    assert history[0].get("content") == msg_payload["content"]

    # 14. Cierre de sesión (Simulado / Borrado de token cliente)
    print("\n[Paso 14] Simulando cierre de sesión en cliente (descartando tokens)...")
    cleared_headers = {}
    print("-> Tokens del cliente borrados. Intentando llamar a /auth/me sin credenciales...")
    status_fail, response_fail = make_request(f"{API_BASE}/auth/me", method="GET", headers=cleared_headers)
    print(f"-> Respuesta esperada de error (HTTP {status_fail}):")
    print(response_fail)
    assert status_fail == 401, "La consulta debió fallar con HTTP 401 Unauthorized debido al logout (sin token)."

    print("\n=========================================================================")
    print("  ¡ÉXITO INTEGRAL! EL FLUJO E2E DESDE SIGNUP HASTA LOGOUT FUNCIONA OK ")
    print("=========================================================================")


if __name__ == "__main__":
    asyncio.run(run_complete_flow_test())
