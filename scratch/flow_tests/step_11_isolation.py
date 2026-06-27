import asyncio
from scratch.flow_tests.common import API_BASE, make_request, get_verification_token


async def run_isolation_tests_step() -> None:
    print("\n=========================================================================")
    print("  [PASO 11] INICIANDO PRUEBAS DE AISLAMIENTO MULTI-TENANT (3 CLÍNICAS)")
    print("=========================================================================")

    # 1. Datos de prueba para 3 clínicas
    clinics_data = [
        {"email": "owner.clinica1@sanjose.com", "password": "PasswordSeguroC1!", "name": "Dr. Uno", "tenant_name": "Clinica Dental San Jose"},
        {"email": "owner.clinica2@delvalle.com", "password": "PasswordSeguroC2!", "name": "Dra. Dos", "tenant_name": "Clinica Medica Del Valle"},
        {"email": "owner.clinica3@pedregal.com", "password": "PasswordSeguroC3!", "name": "Dr. Tres", "tenant_name": "Clinica Oftalmologica Pedregal"}
    ]

    tokens = []
    tenant_ids = []
    headers = []

    # 2. Registrar y activar las 3 clínicas secuencialmente
    for i, data in enumerate(clinics_data, start=1):
        print(f"\n--- Registrando Clínica {i}: '{data['tenant_name']}' ---")
        
        # Pre-registro
        token = await run_register_substep(data["email"], data["password"], data["name"], data["tenant_name"])
        tokens.append(token)

        # Verificación
        tenant_id = await run_verify_substep(data["email"], token)
        tenant_ids.append(tenant_id)

    # Esperar a que se completen de crear los usuarios de forma asíncrona por el worker RabbitMQ
    print("\nEsperando 2 segundos para la creación asíncrona de los 3 usuarios OWNER...")
    await asyncio.sleep(2)

    # 3. Login de los 3 Owners para obtener sus headers de autenticación
    for i, data in enumerate(clinics_data, start=1):
        print(f"Autenticando OWNER de Clínica {i}...")
        owner_headers = await run_login_substep(data["email"], data["password"])
        headers.append(owner_headers)

    h1, h2, h3 = headers[0], headers[1], headers[2]
    t1_id, t2_id, t3_id = tenant_ids[0], tenant_ids[1], tenant_ids[2]

    print("\n--- [Aislamiento 1] Creando servicios en Clínica 1 y Clínica 2 ---")
    
    # Crear servicio en Clínica 1
    status_s1, service1 = make_request(
        f"{API_BASE}/services/",
        method="POST",
        data={"name": "Ortodoncia C1", "description": "Servicio de la clinica 1", "durationMinutes": 60, "price": 1500.0, "currency": "MXN"},
        headers=h1
    )
    assert status_s1 == 201
    s1_id = service1.get("id")
    print(f"-> C1: Servicio creado con ID {s1_id}")

    # Crear servicio en Clínica 2
    status_s2, service2 = make_request(
        f"{API_BASE}/services/",
        method="POST",
        data={"name": "Endodoncia C2", "description": "Servicio de la clinica 2", "durationMinutes": 45, "price": 2000.0, "currency": "MXN"},
        headers=h2
    )
    assert status_s2 == 201
    s2_id = service2.get("id")
    print(f"-> C2: Servicio creado con ID {s2_id}")

    await asyncio.sleep(0.2)

    print("\n--- [Aislamiento 2] Pruebas de acceso cruzado a Servicios (Debe dar 404) ---")
    
    # Clínica 2 intenta leer el servicio de la Clínica 1
    status_get, resp_get = make_request(f"{API_BASE}/services/{s1_id}", method="GET", headers=h2)
    print(f"-> C2 intenta leer Servicio C1: HTTP {status_get} (Esperado: 404)")
    assert status_get == 404

    # Clínica 3 intenta leer el servicio de la Clínica 1
    status_get3, resp_get3 = make_request(f"{API_BASE}/services/{s1_id}", method="GET", headers=h3)
    print(f"-> C3 intenta leer Servicio C1: HTTP {status_get3} (Esperado: 404)")
    assert status_get3 == 404

    # Clínica 2 intenta modificar el servicio de la Clínica 1
    status_put, resp_put = make_request(
        f"{API_BASE}/services/{s1_id}",
        method="PUT",
        data={"name": "Hackeado", "description": "Modificacion maliciosa", "durationMinutes": 30, "price": 10.0, "currency": "MXN", "isActive": True},
        headers=h2
    )
    print(f"-> C2 intenta modificar Servicio C1: HTTP {status_put} (Esperado: 404)")
    assert status_put == 404

    # Clínica 3 intenta eliminar el servicio de la Clínica 1
    status_del, resp_del = make_request(f"{API_BASE}/services/{s1_id}", method="DELETE", headers=h3)
    print(f"-> C3 intenta eliminar Servicio C1: HTTP {status_del} (Esperado: 404)")
    assert status_del == 404

    print("\n--- [Aislamiento 3] Creando clientes en Clínica 1 y Clínica 2 ---")
    
    # Crear cliente en Clínica 1
    status_c1, customer1 = make_request(
        f"{API_BASE}/customers/",
        method="POST",
        data={"phone": "+5215551111111", "name": "Paciente C1", "email": "pacientec1@gmail.com"},
        headers=h1
    )
    assert status_c1 == 201
    c1_id = customer1.get("id")
    print(f"-> C1: Cliente creado con ID {c1_id}")

    # Crear cliente en Clínica 2
    status_c2, customer2 = make_request(
        f"{API_BASE}/customers/",
        method="POST",
        data={"phone": "+5215552222222", "name": "Paciente C2", "email": "pacientec2@gmail.com"},
        headers=h2
    )
    assert status_c2 == 201
    c2_id = customer2.get("id")
    print(f"-> C2: Cliente creado con ID {c2_id}")

    await asyncio.sleep(0.2)

    print("\n--- [Aislamiento 4] Pruebas de acceso cruzado a Clientes (Debe dar 404) ---")
    
    # Clínica 2 intenta leer cliente de Clínica 1
    status_c_get, resp_c_get = make_request(f"{API_BASE}/customers/{c1_id}", method="GET", headers=h2)
    print(f"-> C2 intenta leer Cliente C1: HTTP {status_c_get} (Esperado: 404)")
    assert status_c_get == 404

    # Clínica 2 intenta modificar cliente de Clínica 1
    status_c_put, resp_c_put = make_request(
        f"{API_BASE}/customers/{c1_id}",
        method="PUT",
        data={"name": "Modificado Maliciosamente", "email": "hacked@gmail.com", "leadStatus": "BLOCKED"},
        headers=h2
    )
    print(f"-> C2 intenta modificar Cliente C1: HTTP {status_c_put} (Esperado: 404)")
    assert status_c_put == 404

    # Clínica 3 intenta eliminar cliente de Clínica 1
    status_c_del, resp_c_del = make_request(f"{API_BASE}/customers/{c1_id}", method="DELETE", headers=h3)
    print(f"-> C3 intenta eliminar Cliente C1: HTTP {status_c_del} (Esperado: 404)")
    assert status_c_del == 404

    print("\n--- [Aislamiento 5] Pruebas de coincidencia de Teléfono entre clínicas ---")
    
    # Clínica 2 registra cliente con el MISMO teléfono que Clínica 1
    print("C2 intenta registrar un cliente con el mismo teléfono de C1 (+5215551111111)...")
    status_c2_dup, customer2_dup = make_request(
        f"{API_BASE}/customers/",
        method="POST",
        data={"phone": "+5215551111111", "name": "Paciente Duplicado en C2", "email": "dup@gmail.com"},
        headers=h2
    )
    print(f"-> C2 registra teléfono idéntico: HTTP {status_c2_dup} (Esperado: 201)")
    assert status_c2_dup == 201, "Las clínicas distintas deben poder tener clientes con el mismo teléfono."
    c2_dup_id = customer2_dup.get("id")

    # Clínica 1 intenta registrar el MISMO teléfono nuevamente
    print("C1 intenta registrar un cliente duplicado internamente (+5215551111111)...")
    status_c1_dup, resp_c1_dup = make_request(
        f"{API_BASE}/customers/",
        method="POST",
        data={"phone": "+5215551111111", "name": "Paciente Duplicado Interno", "email": "dup_interno@gmail.com"},
        headers=h1
    )
    print(f"-> C1 registra teléfono interno duplicado: HTTP {status_c1_dup} (Esperado: 409)")
    assert status_c1_dup == 409, "Un mismo negocio no puede registrar duplicados de teléfono."

    # Limpieza de recursos de prueba
    print("\n--- Limpiando recursos de prueba ---")
    await make_delete(f"{API_BASE}/services/{s1_id}", h1)
    await make_delete(f"{API_BASE}/services/{s2_id}", h2)
    await make_delete(f"{API_BASE}/customers/{c1_id}", h1)
    await make_delete(f"{API_BASE}/customers/{c2_id}", h2)
    await make_delete(f"{API_BASE}/customers/{c2_dup_id}", h2)

    print("-> ¡Todas las pruebas de aislamiento multi-tenant pasaron exitosamente!")


async def run_register_substep(email: str, password: str, name: str, tenant_name: str) -> str:
    register_payload = {"email": email, "password": password, "name": name, "tenantName": tenant_name}
    status, response = make_request(f"{API_BASE}/auth/register", data=register_payload, method="POST")
    assert status == 202
    token = await get_verification_token(email)
    assert token is not None
    return token


async def run_verify_substep(email: str, token: str) -> str:
    verify_payload = {"email": email, "token": token}
    status, response = make_request(f"{API_BASE}/auth/verify", data=verify_payload, method="POST")
    assert status == 201
    return response.get("id")


async def run_login_substep(email: str, password: str) -> dict:
    login_payload = {"email": email, "password": password}
    status, response = make_request(f"{API_BASE}/auth/login", data=login_payload, method="POST")
    assert status == 200
    return {"Authorization": f"Bearer {response.get('accessToken')}"}


async def make_delete(url: str, headers: dict) -> None:
    status, _ = make_request(url, method="DELETE", headers=headers)
    assert status == 200
    await asyncio.sleep(0.1)
