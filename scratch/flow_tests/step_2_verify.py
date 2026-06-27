import json
from scratch.flow_tests.common import API_BASE, make_request


async def run_verify_step(email: str, token: str) -> str:
    print("\n--- [PASO 2] VERIFICACIÓN DEL CÓDIGO DE CORREO ---")
    print(f"Verificando correo '{email}' con el token '{token}'...")
    
    verify_payload = {
        "email": email,
        "token": token
    }
    
    status, response = make_request(
        f"{API_BASE}/auth/verify",
        data=verify_payload,
        method="POST"
    )
    
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada del servidor (HTTP {status}): {response}")
        
    print(f"-> Respuesta HTTP {status}:")
    print(json.dumps(response, indent=2))
    assert status == 201, f"La verificación debió retornar HTTP 201 Created. Respuesta: {response}"
    
    tenant_id = response.get("id")
    assert tenant_id is not None, "El tenant ID no debe ser nulo."
    
    return tenant_id
