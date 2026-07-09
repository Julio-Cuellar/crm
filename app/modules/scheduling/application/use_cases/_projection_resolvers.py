"""Helpers compartidos por create_appointment/update_appointment para resolver
Customer/Service contra la proyección local, con fallback HTTP síncrono (PHASE1-SHIM)
cuando la proyección todavía no refleja un registro recién creado en otro módulo."""
import uuid
from decimal import Decimal

from app.modules.scheduling.infrastructure.db.repositories.customer_projection_repository import (
    CustomerProjectionRepository,
)
from app.modules.scheduling.infrastructure.db.repositories.service_projection_repository import (
    ServiceProjectionRepository,
)
from app.modules.scheduling.infrastructure.gateways.customers_fallback_gateway import CustomersFallbackGateway
from app.modules.scheduling.infrastructure.gateways.catalog_fallback_gateway import CatalogFallbackGateway
from app.modules.scheduling.domain.exceptions.appointments import (
    RelatedCustomerNotFoundException,
    RelatedServiceNotFoundException,
)
from app.platform.exceptions import AppException


async def ensure_customer_projected(
    repo: CustomerProjectionRepository,
    gateway: CustomersFallbackGateway,
    customer_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> None:
    projection = await repo.get_by_id(customer_id)
    if projection and projection.tenant_id == tenant_id:
        return
    try:
        data = await gateway.get_customer(customer_id)
    except Exception:
        raise AppException(503, "CUSTOMERS_UNAVAILABLE", "No se pudo validar el cliente, intente de nuevo.")
    if not data or data.get("tenantId") != str(tenant_id):
        raise RelatedCustomerNotFoundException()
    await repo.upsert(
        customer_id=customer_id,
        tenant_id=tenant_id,
        name=data.get("name", ""),
        phone=data.get("phone", ""),
        email=data.get("email"),
        source_updated_at=None,
    )


async def ensure_service_projected(
    repo: ServiceProjectionRepository,
    gateway: CatalogFallbackGateway,
    service_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> None:
    projection = await repo.get_by_id(service_id)
    if projection and projection.tenant_id == tenant_id:
        return
    try:
        data = await gateway.get_service(service_id)
    except Exception:
        raise AppException(503, "CATALOG_UNAVAILABLE", "No se pudo validar el servicio, intente de nuevo.")
    if not data or data.get("tenantId") != str(tenant_id):
        raise RelatedServiceNotFoundException()
    price = data.get("price")
    await repo.upsert(
        service_id=service_id,
        tenant_id=tenant_id,
        name=data.get("name", ""),
        duration_minutes=data.get("durationMinutes", 60),
        price=Decimal(str(price)) if price is not None else None,
        currency=data.get("currency", "MXN"),
        is_active=data.get("isActive", True),
        source_updated_at=None,
    )
