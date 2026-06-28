import re
import uuid
from app.domain.entities.customer import Customer
from app.domain.ports.customer_repository import CustomerRepository
from app.domain.exceptions.customers import CustomerAlreadyExistsException


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits:
        return f"+{digits}"
    return phone.strip()


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
        phone_clean = _normalize_phone(phone)
        
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
