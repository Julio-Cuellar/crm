import uuid
from app.domain.entities.customer import Customer
from app.domain.ports.customer_repository import CustomerRepository


class ListCustomersUseCase:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    async def execute(self, tenant_id: uuid.UUID) -> list[Customer]:
        return await self.customer_repository.get_by_tenant(tenant_id)
