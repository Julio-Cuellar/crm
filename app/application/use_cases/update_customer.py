import uuid
from app.domain.entities.customer import Customer
from app.domain.ports.customer_repository import CustomerRepository
from app.domain.exceptions.customers import CustomerNotFoundException


class UpdateCustomerUseCase:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

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
        
        return await self.customer_repository.save(customer)
