import re
import uuid
from app.domain.entities.customer import Customer
from app.domain.ports.customer_repository import CustomerRepository


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits:
        return f"+{digits}"
    return phone.strip()


class UpsertCustomerUseCase:
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
        customer = await self.customer_repository.get_by_phone_and_tenant(phone_clean, tenant_id)
        
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
            
        return await self.customer_repository.save(customer)
