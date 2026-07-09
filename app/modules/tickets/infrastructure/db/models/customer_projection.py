import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.platform.db.base_class import Base


class CustomerProjection(Base):
    """Copia local, mínima (id/tenant_id/nombre) de Customer — solo lo que `tickets`
    necesita para validar pertenencia al tenant al crear/listar tickets. Mantenida
    por eventos `customer.created/updated/deleted` del módulo `customers`."""

    __tablename__ = "tickets_customer_projection"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
