import uuid
from app.domain.entities.customer import Customer
from app.domain.ports.customer_repository import CustomerRepository
from app.domain.exceptions.customers import CustomerNotFoundException


class UpdateCustomerPipelineUseCase:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    async def execute(
        self,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        pipeline_stage: str,
        deal_value: float | None
    ) -> Customer:
        customer = await self.customer_repository.get_by_id(customer_id)

        if not customer or customer.tenant_id != tenant_id:
            raise CustomerNotFoundException()

        customer.update_pipeline(pipeline_stage=pipeline_stage, deal_value=deal_value)

        return await self.customer_repository.save(customer)
