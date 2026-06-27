from scratch.flow_tests.common import API_BASE, make_request


async def run_services_crud_step(owner_headers: dict, staff_headers: dict) -> None:
    print("\n--- [PASO 9] PRUEBAS DE CATÁLOGO DE SERVICIOS (CRUD & ROLES) ---")

    # 1. Crear un servicio como OWNER (HTTP 201)
    print("1. Creando un servicio como OWNER...")
    service_payload = {
        "name": "Limpieza Dental Completa",
        "description": "Limpieza con ultrasonido y pulido dental completo.",
        "durationMinutes": 45,
        "price": 850.00,
        "currency": "MXN"
    }
    status, response = make_request(
        f"{API_BASE}/services/",
        method="POST",
        data=service_payload,
        headers=owner_headers
    )
    if not isinstance(response, dict):
        raise ValueError(f"Respuesta inesperada al crear servicio (HTTP {status}): {response}")
        
    print(f"   -> Servicio creado (HTTP {status}): ID={response.get('id')}, Nombre='{response.get('name')}'")
    assert status == 201, "Debió retornar HTTP 201 Created."
    service_id = response.get("id")
    assert service_id is not None
    assert float(response.get("price")) == 850.0

    # 2. Modificar el servicio como OWNER (HTTP 200)
    print("2. Modificando detalles del servicio como OWNER...")
    update_payload = {
        "name": "Limpieza Dental Completa + Flúor",
        "description": "Limpieza con ultrasonido, pulido y aplicación de flúor protector.",
        "durationMinutes": 60,
        "price": 1100.00,
        "currency": "MXN",
        "isActive": True
    }
    status_put, response_put = make_request(
        f"{API_BASE}/services/{service_id}",
        method="PUT",
        data=update_payload,
        headers=owner_headers
    )
    print(f"   -> Servicio actualizado (HTTP {status_put}): Nombre='{response_put.get('name')}', Precio={response_put.get('price')}")
    assert status_put == 200, "Debió retornar HTTP 200 OK."
    assert response_put.get("name") == "Limpieza Dental Completa + Flúor"
    assert float(response_put.get("price")) == 1100.0

    # 3. Listar servicios como STAFF (HTTP 200)
    print("3. Listando el catálogo de servicios como STAFF...")
    status_list, response_list = make_request(
        f"{API_BASE}/services/",
        method="GET",
        headers=staff_headers
    )
    if not isinstance(response_list, list):
        raise ValueError(f"Respuesta inesperada al listar servicios (HTTP {status_list}): {response_list}")
        
    print(f"   -> Catálogo listado (HTTP {status_list}): {len(response_list)} servicio(s) encontrado(s).")
    assert status_list == 200, "Debió retornar HTTP 200 OK."
    # Comprobar que nuestro servicio esté en la lista
    found = any(s.get("id") == service_id for s in response_list)
    assert found, "El servicio creado no fue encontrado en la lista del catálogo."

    # 4. Obtener detalles de un servicio específico como STAFF (HTTP 200)
    print("4. Obteniendo detalles de un servicio específico como STAFF...")
    status_get, response_get = make_request(
        f"{API_BASE}/services/{service_id}",
        method="GET",
        headers=staff_headers
    )
    print(f"   -> Detalles obtenidos (HTTP {status_get}): Nombre='{response_get.get('name')}', Duración={response_get.get('durationMinutes')} mins")
    assert status_get == 200, "Debió retornar HTTP 200 OK."
    assert response_get.get("name") == "Limpieza Dental Completa + Flúor"

    # 5. Seguridad: Colaborador (STAFF) intenta escribir en el catálogo (HTTP 403 Forbidden)
    print("5. Verificando que STAFF no tenga permisos de escritura...")
    
    # 5a. Crear servicio
    status_s1, response_s1 = make_request(
        f"{API_BASE}/services/",
        method="POST",
        data=service_payload,
        headers=staff_headers
    )
    print(f"   -> Intentar crear: HTTP {status_s1} (Esperado: 403)")
    assert status_s1 == 403, "STAFF debió recibir HTTP 403 Forbidden al crear."

    # 5b. Modificar servicio
    status_s2, response_s2 = make_request(
        f"{API_BASE}/services/{service_id}",
        method="PUT",
        data=update_payload,
        headers=staff_headers
    )
    print(f"   -> Intentar modificar: HTTP {status_s2} (Esperado: 403)")
    assert status_s2 == 403, "STAFF debió recibir HTTP 403 Forbidden al modificar."

    # 5c. Eliminar servicio
    status_s3, response_s3 = make_request(
        f"{API_BASE}/services/{service_id}",
        method="DELETE",
        headers=staff_headers
    )
    print(f"   -> Intentar eliminar: HTTP {status_s3} (Esperado: 403)")
    assert status_s3 == 403, "STAFF debió recibir HTTP 403 Forbidden al eliminar."

    # 6. Eliminar servicio como OWNER (HTTP 200)
    print("6. Eliminando el servicio del catálogo como OWNER...")
    status_del, response_del = make_request(
        f"{API_BASE}/services/{service_id}",
        method="DELETE",
        headers=owner_headers
    )
    print(f"   -> Respuesta de eliminación (HTTP {status_del}): {response_del.get('message')}")
    assert status_del == 200, "Debió retornar HTTP 200 OK."

    # 7. Verificar que el servicio fue eliminado (HTTP 404 Not Found)
    print("7. Intentando consultar el servicio eliminado...")
    status_v, response_v = make_request(
        f"{API_BASE}/services/{service_id}",
        method="GET",
        headers=owner_headers
    )
    print(f"   -> Consulta posterior a eliminación (HTTP {status_v}): {response_v.get('detail', {}).get('message')}")
    assert status_v == 404, "La consulta debió fallar con HTTP 404 Not Found."

    print("-> ¡Todas las pruebas del catálogo de servicios pasaron exitosamente!")
