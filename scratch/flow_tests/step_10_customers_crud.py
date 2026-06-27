import asyncio
from scratch.flow_tests.common import API_BASE, make_request


async def run_customers_crud_step(owner_headers: dict, staff_headers: dict) -> None:
    print("\n--- [PASO 10] PRUEBAS DE GESTIÓN DE CLIENTES (CRUD, UPSERT & CONFLICTOS) ---")

    # 1. Crear un cliente como STAFF (HTTP 201)
    print("1. Creando un cliente nuevo como STAFF...")
    customer_payload = {
        "phone": "+5215551234567",
        "name": "Maria Lopez",
        "email": "maria.lopez@gmail.com"
    }
    status, response = make_request(
        f"{API_BASE}/customers/",
        method="POST",
        data=customer_payload,
        headers=staff_headers
    )
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada al crear cliente (HTTP {status}): {response}")
        
    print(f"   -> Cliente creado (HTTP {status}): ID={response.get('id')}, Nombre='{response.get('name')}', Estado={response.get('leadStatus')}")
    assert status == 201, "Debió retornar HTTP 201 Created."
    customer_id = response.get("id")
    assert customer_id is not None
    assert response.get("leadStatus") == "NEW"

    # Esperar a que se asiente la transacción
    await asyncio.sleep(0.2)

    # 2. Modificar el cliente como STAFF (HTTP 200)
    print("2. Modificando detalles del cliente y su estado como STAFF...")
    update_payload = {
        "name": "Maria Lopez de Gomez",
        "email": "maria.gomez@gmail.com",
        "leadStatus": "ACTIVE"
    }
    status_put, response_put = make_request(
        f"{API_BASE}/customers/{customer_id}",
        method="PUT",
        data=update_payload,
        headers=staff_headers
    )
    print(f"   -> Cliente actualizado (HTTP {status_put}): Nombre='{response_put.get('name')}', Estado={response_put.get('leadStatus')}")
    assert status_put == 200, "Debió retornar HTTP 200 OK."

    # Esperar a que se asiente la transacción
    await asyncio.sleep(0.2)
    assert response_put.get("name") == "Maria Lopez de Gomez"
    assert response_put.get("leadStatus") == "ACTIVE"

    # 3. Upsert del cliente con mismo teléfono (HTTP 200)
    print("3. Ejecutando Upsert del cliente con el mismo teléfono (debería actualizarse)...")
    upsert_payload = {
        "phone": "+5215551234567",
        "name": "Maria L. Gomez (Actualizada)",
        "email": "maria.gomez.new@gmail.com"
    }
    status_up, response_up = make_request(
        f"{API_BASE}/customers/upsert",
        method="POST",
        data=upsert_payload,
        headers=staff_headers
    )
    print(f"   -> Respuesta de Upsert (HTTP {status_up}): Nombre='{response_up.get('name')}', Email='{response_up.get('email')}'")
    assert status_up == 200, "Debió retornar HTTP 200 OK."
    assert response_up.get("id") == customer_id, "El ID debió ser el mismo del cliente existente."
    assert response_up.get("name") == "Maria L. Gomez (Actualizada)"
    assert response_up.get("email") == "maria.gomez.new@gmail.com"

    # Esperar a que se asiente la transacción
    await asyncio.sleep(0.2)

    # 4. Intentar crear un duplicado directo en el mismo tenant (HTTP 409 Conflict)
    print("4. Intentando registrar un duplicado directo con el mismo teléfono...")
    status_dup, response_dup = make_request(
        f"{API_BASE}/customers/",
        method="POST",
        data=customer_payload,
        headers=staff_headers
    )
    print(f"   -> Respuesta esperada de conflicto (HTTP {status_dup}): {response_dup.get('detail', {}).get('message')}")
    assert status_dup == 409, "Debió retornar HTTP 409 Conflict."

    # 5. Listar clientes (HTTP 200)
    print("5. Listando todos los clientes del tenant...")
    status_list, response_list = make_request(
        f"{API_BASE}/customers/",
        method="GET",
        headers=staff_headers
    )
    if not isinstance(response_list, list):
        raise ValueError(f"Respuesta inesperada al listar clientes (HTTP {status_list}): {response_list}")
        
    print(f"   -> Clientes listados (HTTP {status_list}): {len(response_list)} cliente(s) encontrado(s).")
    assert status_list == 200, "Debió retornar HTTP 200 OK."
    found = any(c.get("id") == customer_id for c in response_list)
    assert found, "El cliente creado no se encuentra en la lista."

    # 6. Consultar detalles de cliente específico (HTTP 200)
    print("6. Consultando detalles de un cliente específico...")
    status_get, response_get = make_request(
        f"{API_BASE}/customers/{customer_id}",
        method="GET",
        headers=staff_headers
    )
    print(f"   -> Detalles obtenidos (HTTP {status_get}): Nombre='{response_get.get('name')}', Teléfono='{response_get.get('phone')}'")
    assert status_get == 200, "Debió retornar HTTP 200 OK."
    assert response_get.get("name") == "Maria L. Gomez (Actualizada)"

    # 7. Eliminar cliente (HTTP 200)
    print("7. Eliminando cliente...")
    status_del, response_del = make_request(
        f"{API_BASE}/customers/{customer_id}",
        method="DELETE",
        headers=staff_headers
    )
    print(f"   -> Respuesta de eliminación (HTTP {status_del}): {response_del.get('message')}")
    assert status_del == 200, "Debió retornar HTTP 200 OK."

    # Esperar a que se asiente la transacción
    await asyncio.sleep(0.2)

    # 8. Verificar que el cliente fue eliminado (HTTP 404 Not Found)
    print("8. Verificando que la consulta de cliente eliminado retorne 404...")
    status_v, response_v = make_request(
        f"{API_BASE}/customers/{customer_id}",
        method="GET",
        headers=staff_headers
    )
    print(f"   -> Consulta posterior a eliminación (HTTP {status_v}): {response_v.get('detail', {}).get('message')}")
    assert status_v == 404, "La consulta debió fallar con HTTP 404 Not Found."

    print("-> ¡Todas las pruebas de gestión de clientes pasaron exitosamente!")
