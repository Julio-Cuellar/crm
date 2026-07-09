import uuid
from app.modules.customers.domain.ports.customer_repository import CustomerRepository
from app.modules.customers.domain.exceptions.customers import CustomerNotFoundException
from app.modules.customers.infrastructure.messaging.publishers import publish_customer_deleted
from app.platform.messaging.event_bus import EventBus


class DeleteCustomerUseCase:
    def __init__(self, customer_repository: CustomerRepository, event_bus: EventBus | None = None):
        self.customer_repository = customer_repository
        self.event_bus = event_bus

    async def execute(self, customer_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        customer = await self.customer_repository.get_by_id(customer_id)

        # Validar existencia y scope de tenant
        if not customer or customer.tenant_id != tenant_id:
            raise CustomerNotFoundException()

        deleted = await self.customer_repository.delete(customer_id)
        if deleted:
            await publish_customer_deleted(self.event_bus, customer_id, tenant_id)
        return deleted
