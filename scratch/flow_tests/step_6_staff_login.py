from scratch.flow_tests.common import API_BASE, make_request


async def run_staff_login_and_logout_step(staff_email: str, staff_password: str, tenant_id: str) -> None:
    print("\n--- [PASO 6] INICIO DE SESIÓN Y VERIFICACIÓN DEL STAFF ---")
    print(f"Autenticando al STAFF '{staff_email}'...")
    
    login_payload = {
        "email": staff_email,
        "password": staff_password
    }
    
    status, response = make_request(
        f"{API_BASE}/auth/login",
        data=login_payload,
        method="POST"
    )
    
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada del servidor (HTTP {status}): {response}")
        
    print(f"-> Respuesta HTTP {status}: Login Exitoso.")
    assert status == 200, f"El login de STAFF debió retornar HTTP 200. Respuesta: {response}"
    
    staff_access_token = response.get("accessToken")
    assert staff_access_token is not None
    staff_headers = {"Authorization": f"Bearer {staff_access_token}"}

    # Verificar perfil
    status_me, response_me = make_request(
        f"{API_BASE}/auth/me",
        method="GET",
        headers=staff_headers
    )
    
    if not isinstance(response_me, dict):
        raise ValueError(f"Respuesta inesperada del servidor (HTTP {status_me}): {response_me}")
        
    print(f"-> Perfil consultado (HTTP {status_me}):")
    print(f"   Nombre: {response_me.get('name')}")
    print(f"   Email: {response_me.get('email')}")
    print(f"   Rol: {response_me.get('role')}")
    print(f"   Tenant ID: {response_me.get('tenantId')}")
    assert status_me == 200
    assert response_me.get("role") == "STAFF"
    assert response_me.get("tenantId") == tenant_id

    # Listar usuarios
    print(f"\n[Paso 6b] Listando usuarios del tenant como STAFF...")
    status_users, response_users = make_request(
        f"{API_BASE}/users/",
        method="GET",
        headers=staff_headers
    )
    
    if not isinstance(response_users, list):
        raise ValueError(f"Respuesta inesperada del servidor al listar usuarios (HTTP {status_users}): {response_users}")
        
    print(f"-> Lista de usuarios (HTTP {status_users}):")
    for u in response_users:
        print(f"   - {u.get('name')} ({u.get('email')}) - Rol: {u.get('role')}")
    assert status_users == 200
    assert len(response_users) == 2, "Deben haber exactamente 2 usuarios en el tenant."

    return staff_headers
