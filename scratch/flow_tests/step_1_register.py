from scratch.flow_tests.common import API_BASE, make_request, get_verification_token


async def run_register_step(email: str, password: str, name: str, tenant_name: str) -> str:
    print("\n--- [PASO 1] PRE-REGISTRO DEL TENANT ---")
    print(f"Enviando solicitud para: {email} ({tenant_name})...")
    
    register_payload = {
        "email": email,
        "password": password,
        "name": name,
        "tenantName": tenant_name
    }
    
    status, response = make_request(
        f"{API_BASE}/auth/register",
        data=register_payload,
        method="POST"
    )
    
    if status == 0:
        raise ConnectionError(
            f"No se pudo conectar al servidor en {API_BASE}. "
            "Por favor, asegúrese de iniciar uvicorn con: \n"
            "  .venv\\Scripts\\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
        )
        
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada del servidor (HTTP {status}): {response}")
        
    print(f"-> Respuesta HTTP {status}: {response.get('message')}")
    assert status == 202, f"El pre-registro debió retornar HTTP 202. Respuesta: {response}"

    # Obtener el código
    token = await get_verification_token(email)
    print(f"-> Código de verificación recuperado de DB: {token}")
    assert token is not None, "El código de verificación no debe ser nulo."
    
    return token
