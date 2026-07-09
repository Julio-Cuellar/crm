import asyncio
import sys
import os

# Agrega la carpeta /backend al PATH de búsqueda de Python para poder importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.platform.db.session import init_db

# Importación de cada paso modular
from scratch.flow_tests.step_1_register import run_register_step
from scratch.flow_tests.step_2_verify import run_verify_step
from scratch.flow_tests.step_3_owner_login import run_owner_login_step
from scratch.flow_tests.step_4_invite import run_invite_step
from scratch.flow_tests.step_5_accept import run_accept_step
from scratch.flow_tests.step_6_staff_login import run_staff_login_and_logout_step
from scratch.flow_tests.step_7_exceptions import run_exceptions_step
from scratch.flow_tests.step_8_logout import run_logout_step
from scratch.flow_tests.step_9_services_crud import run_services_crud_step
from scratch.flow_tests.step_10_customers_crud import run_customers_crud_step
from scratch.flow_tests.step_11_isolation import run_isolation_tests_step


async def main():
    print("=========================================================================")
    print("  INICIANDO SUITE DE PRUEBAS MODULARES DE FLUJO COMPLETO (E2E FLOWS)")
    print("=========================================================================")

    # 1. Reiniciar base de datos
    print("\n[Inicialización] Limpiando Postgres...")
    await init_db()
    print("-> Base de datos limpia.")

    # Datos de prueba
    email = "alejandro.gomez@dentalsanjose.com"
    password = "PasswordOwnerSeguro123"
    name = "Dr. Alejandro Gomez"
    tenant_name = "Dental San Jose Clinic"

    staff_email = "carlos.staff@dentalsanjose.com"
    staff_name = "Carlos Asistente"
    staff_password = "PasswordStaff123"

    # PASO 1: Pre-registro y obtención de token
    verif_token = await run_register_step(
        email=email,
        password=password,
        name=name,
        tenant_name=tenant_name
    )

    # PASO 2: Confirmar verificación y materializar tenant
    tenant_id = await run_verify_step(
        email=email,
        token=verif_token
    )

    # Esperar 2 segundos para dar tiempo al worker RabbitMQ de crear el OWNER en Postgres
    print("\nEsperando 2 segundos para la creación asíncrona del usuario OWNER en Postgres...")
    await asyncio.sleep(2)

    # PASO 3: Login OWNER y verificación de perfil
    owner_headers = await run_owner_login_step(
        email=email,
        password=password
    )

    # PASO 4: OWNER invita a STAFF y obtiene token de invitación
    invite_token = await run_invite_step(
        owner_headers=owner_headers,
        staff_email=staff_email
    )

    # PASO 5: STAFF consulta y acepta invitación completando registro
    await run_accept_step(
        invite_token=invite_token,
        staff_name=staff_name,
        staff_password=staff_password
    )

    # Esperar 1 segundo para asegurar la visibilidad de la transacción en Windows
    print("\nEsperando 1 segundo para asegurar la persistencia en disco...")
    await asyncio.sleep(1)

    # PASO 6: STAFF inicia sesión, verifica perfil y lista usuarios
    staff_headers = await run_staff_login_and_logout_step(
        staff_email=staff_email,
        staff_password=staff_password,
        tenant_id=tenant_id
    )

    # PASO 7: Ejecutar pruebas de excepciones (negativas) con tokens activos
    await run_exceptions_step(
        owner_headers=owner_headers,
        staff_headers=staff_headers,
        owner_email=email,
        staff_email=staff_email
    )

    # PASO 9: Ejecutar pruebas de CRUD de servicios y validaciones de rol
    await run_services_crud_step(
        owner_headers=owner_headers,
        staff_headers=staff_headers
    )

    # PASO 10: Ejecutar pruebas de CRUD de clientes y operaciones de Upsert
    await run_customers_crud_step(
        owner_headers=owner_headers,
        staff_headers=staff_headers
    )

    # PASO 11: Ejecutar pruebas de aislamiento Multi-Tenant con 3 clínicas
    await run_isolation_tests_step()

    # PASO 8: Cierre de sesión real en servidor (Logout) para STAFF
    print("\n[Logout] Cerrando sesión del STAFF...")
    await run_logout_step(staff_headers)

    # PASO 9: Cierre de sesión real en servidor (Logout) para OWNER
    print("\n[Logout] Cerrando sesión del OWNER...")
    await run_logout_step(owner_headers)

    print("\n=========================================================================")
    print("   ¡SUITE DE PRUEBAS MODULARES FINALIZADA CON ÉXITO ABSOLUTO (100% OK)!")
    print("=========================================================================")


if __name__ == "__main__":
    asyncio.run(main())
