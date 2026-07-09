import re
import uuid
from app.modules.customers.domain.entities.customer import Customer
from app.modules.customers.domain.ports.customer_repository import CustomerRepository
from app.modules.customers.infrastructure.messaging.publishers import (
    publish_customer_created,
    publish_customer_updated,
)
from app.platform.messaging.event_bus import EventBus


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits:
        return f"+{digits}"
    return phone.strip()


class UpsertCustomerUseCase:
    def __init__(self, customer_repository: CustomerRepository, event_bus: EventBus | None = None):
        self.customer_repository = customer_repository
        self.event_bus = event_bus

    async def execute(
        self,
        tenant_id: uuid.UUID,
        phone: str,
        name: str,
        email: str | None = None
    ) -> Customer:
        phone_clean = _normalize_phone(phone)
        customer = await self.customer_repository.get_by_phone_and_tenant(phone_clean, tenant_id)
        is_new = customer is None

        if customer:
            # Si ya existe, actualiza su información básica
            customer.update_info(name=name, email=email)
        else:
            # Si no existe, lo inicializa como NEW
            customer = Customer(
                tenant_id=tenant_id,
                phone=phone_clean,
                name=name.strip(),
                email=email.strip() if email else None,
                lead_status="NEW"
            )

        saved = await self.customer_repository.save(customer)
        if is_new:
            await publish_customer_created(self.event_bus, saved)
        else:
            await publish_customer_updated(self.event_bus, saved)
        return saved
