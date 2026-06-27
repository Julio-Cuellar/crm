from scratch.flow_tests.common import API_BASE, make_request, get_invitation_token


async def run_invite_step(owner_headers: dict, staff_email: str, staff_role: str = "STAFF") -> str:
    print(f"\n--- [PASO 4] PROPIETARIO INVITA A COLABORADOR ({staff_role}) ---")
    print(f"Enviando invitación a '{staff_email}'...")
    
    invite_payload = {
        "email": staff_email,
        "role": staff_role
    }
    
    status, response = make_request(
        f"{API_BASE}/users/invite",
        data=invite_payload,
        method="POST",
        headers=owner_headers
    )
    
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada del servidor (HTTP {status}): {response}")
        
    print(f"-> Respuesta HTTP {status}: Invitación creada con éxito.")
    assert status == 201, f"La creación de invitación debió retornar HTTP 201. Respuesta: {response}"

    # Obtener token de invitación desde la base de datos
    invite_token = await get_invitation_token(staff_email)
    print(f"-> Token de invitación recuperado de DB: {invite_token}")
    assert invite_token is not None, "El token de invitación no debe ser nulo."
    
    return invite_token
