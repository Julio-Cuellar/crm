import asyncio
import json
import sys
import os
import urllib.request
import urllib.error
import time

# Agrega la carpeta /backend al PATH de búsqueda de Python para poder importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.platform.db.session import async_session_factory
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_pending_registration_repository import SQLAlchemyPendingRegistrationRepository

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


async def get_token_from_db(email: str) -> str | None:
    async with async_session_factory() as session:
        repo = SQLAlchemyPendingRegistrationRepository(session)
        pending = await repo.get_by_email(email)
        return pending.verification_token if pending else None


async def run_tests():
    print("--- INICIANDO PRUEBAS DE ENDPOINTS DE LA API (AUTH Y TENANTS) ---")
    print("Esperando 2 segundos para asegurar conexión con el servidor...")
    await asyncio.sleep(2)

    email = "testowner@dentalsanjose.com"
    password = "MySuperSecretPassword123"
    name = "Dr. Julio Gomez"
    tenant_name = "Dental San Jose Test"

    # 1. POST /auth/register - Solicitar registro
    print("\n[Paso 1] Enviando solicitud de registro a /auth/register...")
    register_payload = {
        "email": email,
        "password": password,
        "name": name,
        "tenantName": tenant_name
    }
    
    status, response = make_request(f"{API_BASE}/auth/register", data=register_payload, method="POST")
    print(f"Respuesta (HTTP {status}):")
    print(json.dumps(response, indent=2))
    
    if status != 202:
        print("ERROR: Falló el pre-registro.")
        return

    # 2. Consultar el código de verificación en la base de datos
    print("\n[Paso 2] Consultando código de verificación en Postgres...")
    token = await get_token_from_db(email)
    print(f"-> Código obtenido de la BD: {token}")
    if not token:
        print("ERROR: No se encontró el código en la base de datos.")
        return

    # 3. POST /auth/verify - Verificar código y materializar
    print(f"\n[Paso 3] Enviando código '{token}' a /auth/verify...")
    verify_payload = {
        "email": email,
        "token": token
    }
    status, response = make_request(f"{API_BASE}/auth/verify", data=verify_payload, method="POST")
    print(f"Respuesta (HTTP {status}):")
    print(json.dumps(response, indent=2))
    
    if status != 201:
        print("ERROR: Falló la verificación del código.")
        return
        
    tenant_id = response.get("id")

    # Esperar 2 segundos para dar tiempo al broker a crear el usuario
    print("\nEsperando 2 segundos para el procesamiento asíncrono en segundo plano...")
    await asyncio.sleep(2)

    # 4. POST /auth/login - Iniciar sesión para obtener JWT
    print("\n[Paso 4] Iniciando sesión en /auth/login...")
    login_payload = {
        "email": email,
        "password": password
    }
    status, response = make_request(f"{API_BASE}/auth/login", data=login_payload, method="POST")
    print(f"Respuesta (HTTP {status}):")
    print(json.dumps(response, indent=2))
    
    if status != 200:
        print("ERROR: Falló el inicio de sesión.")
        return
        
    access_token = response.get("accessToken")
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # 5. GET /auth/me - Consultar perfil protegido actual
    print("\n[Paso 5] Consultando perfil protegido actual en /auth/me...")
    status, response = make_request(f"{API_BASE}/auth/me", method="GET", headers=auth_headers)
    print(f"Respuesta (HTTP {status}):")
    print(json.dumps(response, indent=2))

    # 5b. GET /users/ - Listar usuarios del tenant
    print("\n[Paso 5b] Listando usuarios del tenant en /users/...")
    status, response = make_request(f"{API_BASE}/users/", method="GET", headers=auth_headers)
    print(f"Respuesta (HTTP {status}):")
    print(json.dumps(response, indent=2))

    # 6. GET /tenants/{id} - Consultar configuración comercial del Tenant
    print(f"\n[Paso 6] Consultando configuración del tenant por ID: {tenant_id}...")
    status, response = make_request(f"{API_BASE}/tenants/{tenant_id}", method="GET")
    print(f"Respuesta (HTTP {status}):")
    print(json.dumps(response, indent=2))

    # 7. PUT /tenants/{id} - Actualizar configuración comercial del Tenant
    print(f"\n[Paso 7] Actualizando la configuración del tenant...")
    update_payload = {
        "name": "Dental San Jose Modificado API",
        "slug": "dental-san-jose-mod",
        "phoneNumberId": "meta-whatsapp-new",
        "timezone": "America/Chihuahua",
        "locale": "en"
    }
    status, response = make_request(f"{API_BASE}/tenants/{tenant_id}", data=update_payload, method="PUT")
    print(f"Respuesta (HTTP {status}):")
    print(json.dumps(response, indent=2))

    print("\n--- PRUEBAS DE ENDPOINTS COMPLETADAS CON ÉXITO ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
