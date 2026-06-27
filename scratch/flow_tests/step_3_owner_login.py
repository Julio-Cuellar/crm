from scratch.flow_tests.common import API_BASE, make_request


async def run_owner_login_step(email: str, password: str) -> dict:
    print("\n--- [PASO 3] INICIO DE SESIÓN DEL PROPIETARIO (OWNER) ---")
    print(f"Autenticando al OWNER '{email}'...")
    
    login_payload = {
        "email": email,
        "password": password
    }
    
    status, response = make_request(
        f"{API_BASE}/auth/login",
        data=login_payload,
        method="POST"
    )
    
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada del servidor (HTTP {status}): {response}")
        
    print(f"-> Respuesta HTTP {status}: Login Exitoso.")
    assert status == 200, f"El login de OWNER debió retornar HTTP 200. Respuesta: {response}"
    
    access_token = response.get("accessToken")
    assert access_token is not None
    owner_headers = {"Authorization": f"Bearer {access_token}"}

    # Verificar perfil
    status_me, response_me = make_request(
        f"{API_BASE}/auth/me",
        method="GET",
        headers=owner_headers
    )
    
    if not isinstance(response_me, dict):
        raise ValueError(f"Respuesta inesperada del servidor en /auth/me (HTTP {status_me}): {response_me}")
        
    print(f"-> Perfil consultado (HTTP {status_me}):")
    print(f"   Nombre: {response_me.get('name')}")
    print(f"   Email: {response_me.get('email')}")
    print(f"   Rol: {response_me.get('role')}")
    assert status_me == 200
    assert response_me.get("role") == "OWNER"

    return owner_headers
