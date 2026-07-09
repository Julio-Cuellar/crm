import uuid
from app.modules.customers.domain.entities.customer import Customer
from app.modules.customers.domain.ports.customer_repository import CustomerRepository
from app.modules.customers.domain.exceptions.customers import CustomerNotFoundException
from app.modules.customers.infrastructure.messaging.publishers import publish_customer_updated
from app.platform.messaging.event_bus import EventBus


class UpdateCustomerUseCase:
    def __init__(self, customer_repository: CustomerRepository, event_bus: EventBus | None = None):
        self.customer_repository = customer_repository
        self.event_bus = event_bus

    async def execute(
        self,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        name: str,
        email: str | None,
        lead_status: str
    ) -> Customer:
        customer = await self.customer_repository.get_by_id(customer_id)
        
        # Validar existencia y scope de tenant
        if not customer or customer.tenant_id != tenant_id:
            raise CustomerNotFoundException()

        # Actualizar campos usando reglas de dominio
        customer.update_info(name=name, email=email)
        customer.change_status(lead_status)
        
        saved = await self.customer_repository.save(customer)
        await publish_customer_updated(self.event_bus, saved)
        return saved
