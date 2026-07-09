import asyncio
import sys
import os

# Agrega la carpeta /backend al PATH de búsqueda de Python para poder importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.platform.db.session import async_session_factory, init_db
from app.modules.tenants.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.modules.tenants.application.use_cases.create_tenant import CreateTenantUseCase
from app.modules.tenants.application.use_cases.get_tenant import GetTenantUseCase
from app.modules.tenants.application.use_cases.update_tenant import UpdateTenantUseCase
from app.modules.tenants.domain.exceptions.tenant import TenantSlugAlreadyExistsException, TenantNotFoundException


async def test_tenant_flow():
    print("--- INICIANDO PRUEBA DE INTEGRACIÓN DEL MÓDULO DE TENANTS ---")
    
    # 1. Reiniciar las tablas para la prueba
    await init_db()
    
    async with async_session_factory() as session:
        # Instanciar el repositorio y los casos de uso
        repo = SQLAlchemyTenantRepository(session)
        create_use_case = CreateTenantUseCase(repo)
        get_use_case = GetTenantUseCase(repo)
        update_use_case = UpdateTenantUseCase(repo)

        # 2. Probar creación de Tenant exitosa
        print("\n[Prueba] Creando un nuevo tenant...")
        tenant = await create_use_case.execute(
            name="Consultorio Dental X",
            slug="dental-x",
            phone_number_id="meta-12345",
            timezone="America/Mexico_City",
            locale="es"
        )
        print(f"-> Tenant creado exitosamente:")
        print(f"   ID: {tenant.id}")
        print(f"   Nombre: {tenant.name}")
        print(f"   Slug: {tenant.slug}")
        print(f"   Phone Number ID: {tenant.phone_number_id}")
        print(f"   Zona Horaria: {tenant.timezone}")
        print(f"   Idioma: {tenant.locale}")
        print(f"   Activo: {tenant.is_active}")

        # Confirmamos en base de datos física
        await session.commit()

        # 3. Probar restricción de unicidad del Slug (Excepción esperada)
        print("\n[Prueba] Intentando crear otro tenant con el mismo slug (esperando excepción)...")
        try:
            await create_use_case.execute(
                name="Otro Consultorio Dental",
                slug="dental-x",
                phone_number_id="meta-67890"
            )
            print("-> ERROR: Se permitió registrar un slug duplicado.")
        except TenantSlugAlreadyExistsException as e:
            print(f"-> ÉXITO: Excepción capturada correctamente. Código: {e.code}. Mensaje: {e.message}")

        # 4. Probar obtener el Tenant por ID
        print(f"\n[Prueba] Obteniendo el tenant por su ID ({tenant.id})...")
        fetched_tenant = await get_use_case.execute(tenant.id)
        print(f"-> Tenant obtenido de DB: {fetched_tenant.name} ({fetched_tenant.slug})")

        # 5. Probar error de Tenant Inexistente
        fake_id = tenant.id # Generar un UUID aleatorio
        import uuid
        fake_id = uuid.uuid4()
        print(f"\n[Prueba] Consultando un tenant inexistente ({fake_id}) (esperando excepción)...")
        try:
            await get_use_case.execute(fake_id)
            print("-> ERROR: Se obtuvo un tenant que no existe.")
        except TenantNotFoundException as e:
            print(f"-> ÉXITO: Excepción capturada correctamente. Código: {e.code}. Mensaje: {e.message}")

        # 6. Probar actualización del Tenant
        print(f"\n[Prueba] Actualizando configuración del tenant ({tenant.id})...")
        updated_tenant = await update_use_case.execute(
            tenant_id=tenant.id,
            name="Dental X Modificado",
            slug="dental-x-new",
            phone_number_id="meta-99999",
            timezone="America/Chihuahua",
            locale="en"
        )
        print(f"-> Tenant actualizado exitosamente:")
        print(f"   Nombre: {updated_tenant.name}")
        print(f"   Slug: {updated_tenant.slug}")
        print(f"   Phone Number ID: {updated_tenant.phone_number_id}")
        print(f"   Zona Horaria: {updated_tenant.timezone}")
        print(f"   Idioma: {updated_tenant.locale}")
        print(f"   Actualizado en: {updated_tenant.updated_at}")
        
        await session.commit()

    print("\n--- PRUEBA DE INTEGRACIÓN COMPLETADA CON ÉXITO ---")


if __name__ == "__main__":
    asyncio.run(test_tenant_flow())
