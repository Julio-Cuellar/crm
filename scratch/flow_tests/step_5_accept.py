import json
from scratch.flow_tests.common import API_BASE, make_request


async def run_accept_step(invite_token: str, staff_name: str, staff_password: str) -> None:
    print("\n--- [PASO 5] COLABORADOR CONSULTA Y ACEPTA INVITACIÓN ---")
    
    # Consultar detalles
    print(f"Consultando detalles de la invitación con token '{invite_token}'...")
    status_details, response_details = make_request(
        f"{API_BASE}/auth/invitations/{invite_token}",
        method="GET"
    )
    
    if not isinstance(response_details, dict):
        raise ValueError(f"Respuesta inesperada del servidor (HTTP {status_details}): {response_details}")
        
    print(f"-> Detalles (HTTP {status_details}):")
    print(json.dumps(response_details, indent=2))
    assert status_details == 200, f"La consulta debió retornar HTTP 200. Respuesta: {response_details}"
    
    # Aceptar invitación
    print(f"Enviando registro de aceptación para '{staff_name}'...")
    accept_payload = {
        "token": invite_token,
        "name": staff_name,
        "password": staff_password
    }
    
    status, response = make_request(
        f"{API_BASE}/auth/invitations/accept",
        data=accept_payload,
        method="POST"
    )
    
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada del servidor (HTTP {status}): {response}")
        
    print(f"-> Respuesta HTTP {status}: Colaborador registrado correctamente.")
    assert status == 201, f"La aceptación debió retornar HTTP 201. Respuesta: {response}"
