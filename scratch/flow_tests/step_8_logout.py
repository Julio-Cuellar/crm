from scratch.flow_tests.common import API_BASE, make_request


async def run_logout_step(headers: dict) -> None:
    print("\n--- [PASO 7] CIERRE DE SESIÓN EN EL SERVIDOR (LOGOUT) ---")
    print("Enviando petición de logout a /auth/logout...")
    
    status, response = make_request(
        f"{API_BASE}/auth/logout",
        method="POST",
        headers=headers
    )
    
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada en logout (HTTP {status}): {response}")
        
    print(f"-> Respuesta HTTP {status}: {response.get('message')}")
    assert status == 200, "El cierre de sesión debió retornar HTTP 200."

    # Intentar llamar a /auth/me con el token invalidado
    print("\nIntentando llamar a /auth/me con el mismo token invalidado...")
    status_fail, response_fail = make_request(
        f"{API_BASE}/auth/me",
        method="GET",
        headers=headers
    )
    print(f"-> Respuesta esperada de error (HTTP {status_fail}):")
    print(response_fail)
    assert status_fail == 401, "La consulta debió fallar con HTTP 401 Unauthorized."
