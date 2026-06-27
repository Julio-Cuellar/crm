import asyncio
from scratch.flow_tests.common import API_BASE, make_request


async def run_exceptions_step(
    owner_headers: dict,
    staff_headers: dict,
    owner_email: str,
    staff_email: str
) -> None:
    print("\n--- [PASO 8] PRUEBAS DE EXCEPCIONES Y CASOS NEGATIVOS ---")

    # 1. Login con contraseña incorrecta (HTTP 401)
    print("1. Intentando iniciar sesión con contraseña incorrecta...")
    login_payload = {
        "email": owner_email,
        "password": "WrongPassword123"
    }
    status, response = make_request(f"{API_BASE}/auth/login", data=login_payload, method="POST")
    print(f"   -> Respuesta esperada (HTTP {status}): {response.get('detail', {}).get('message')}")
    assert status == 401, "Debió retornar HTTP 401 Unauthorized."

    # 2. Verificación de correo con código incorrecto (HTTP 400)
    print("2. Intentando verificar correo con un código incorrecto...")
    # Registramos un email temporal para que quede pendiente en la BD
    temp_email = "wrongtoken@dentalsanjose.com"
    reg_payload_temp = {
        "email": temp_email,
        "password": "PasswordTemp123",
        "name": "Temp User",
        "tenantName": "Temp Clinic"
    }
    status_reg, response_reg = make_request(f"{API_BASE}/auth/register", data=reg_payload_temp, method="POST")
    print(f"   -> Registro temporal de prueba (HTTP {status_reg}): {response_reg.get('message') if isinstance(response_reg, dict) else response_reg}")
    
    # Esperar a que se asiente la transacción
    await asyncio.sleep(0.5)

    # Intentar verificar con código erróneo
    verify_payload = {
        "email": temp_email,
        "token": "000000"
    }
    status, response = make_request(f"{API_BASE}/auth/verify", data=verify_payload, method="POST")
    print(f"   -> Respuesta esperada (HTTP {status}): {response.get('detail', {}).get('message')}")
    assert status == 400, "Debió retornar HTTP 400 Bad Request."

    # 3. Pre-registro con un correo que ya existe de forma activa en el sistema (HTTP 409)
    print("3. Intentando pre-registrar un correo que ya tiene cuenta activa...")
    register_payload = {
        "email": owner_email,
        "password": "Password123",
        "name": "Dr. Clon",
        "tenantName": "Clon Clinic"
    }
    status, response = make_request(f"{API_BASE}/auth/register", data=register_payload, method="POST")
    print(f"   -> Respuesta esperada (HTTP {status}): {response.get('detail', {}).get('message')}")
    assert status == 409, "Debió retornar HTTP 409 Conflict."

    # 4. Colaborador (STAFF) intenta invitar a otro usuario (HTTP 403 Forbidden)
    print("4. Colaborador (STAFF) intenta invitar a otro usuario (no permitido)...")
    invite_payload = {
        "email": "nuevo.colaborador@dentalsanjose.com",
        "role": "STAFF"
    }
    status, response = make_request(f"{API_BASE}/users/invite", data=invite_payload, method="POST", headers=staff_headers)
    print(f"   -> Respuesta esperada (HTTP {status}): {response}")
    assert status == 403, "Debió retornar HTTP 403 Forbidden."

    # 5. Intentar invitar a un usuario que ya está registrado de forma activa (HTTP 409)
    print("5. Propietario (OWNER) intenta invitar a un usuario que ya posee cuenta...")
    invite_payload_dup = {
        "email": staff_email,
        "role": "STAFF"
    }
    status, response = make_request(f"{API_BASE}/users/invite", data=invite_payload_dup, method="POST", headers=owner_headers)
    print(f"   -> Respuesta esperada (HTTP {status}): {response.get('detail', {}).get('message')}")
    assert status == 409, "Debió retornar HTTP 409 Conflict."

    # 6. Consultar detalles de invitación con un token inválido (HTTP 404)
    print("6. Intentando consultar detalles de una invitación inexistente...")
    fake_token = "invalid-token-uuid-12345"
    status, response = make_request(f"{API_BASE}/auth/invitations/{fake_token}", method="GET")
    print(f"   -> Respuesta esperada (HTTP {status}): {response.get('detail', {}).get('message')}")
    assert status == 404, "Debió retornar HTTP 404 Not Found."

    # 7. Aceptar invitación con un token inexistente (HTTP 404)
    print("7. Intentando aceptar una invitación con un token inexistente...")
    accept_payload = {
        "token": fake_token,
        "name": "Intruso",
        "password": "PasswordIntruso123"
    }
    status, response = make_request(f"{API_BASE}/auth/invitations/accept", data=accept_payload, method="POST")
    print(f"   -> Respuesta esperada (HTTP {status}): {response.get('detail', {}).get('message')}")
    assert status == 404, "Debió retornar HTTP 404 Not Found."

    print("-> ¡Todas las pruebas de excepciones y casos negativos pasaron exitosamente!")
