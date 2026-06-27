import uuid
from app.domain.entities.customer import Customer
from app.domain.ports.customer_repository import CustomerRepository
from app.domain.exceptions.customers import CustomerAlreadyExistsException


class CreateCustomerUseCase:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    async def execute(
        self,
        tenant_id: uuid.UUID,
        phone: str,
        name: str,
        email: str | None = None
    ) -> Customer:
        phone_clean = phone.strip()
        
        # Validar si ya existe este número de teléfono registrado en el mismo negocio
        existing = await self.customer_repository.get_by_phone_and_tenant(phone_clean, tenant_id)
        if existing:
            raise CustomerAlreadyExistsException(
                f"El número de teléfono '{phone_clean}' ya se encuentra registrado para este negocio."
            )

        customer = Customer(
            tenant_id=tenant_id,
            phone=phone_clean,
            name=name.strip(),
            email=email.strip() if email else None
        )
        return await self.customer_repository.save(customer)
