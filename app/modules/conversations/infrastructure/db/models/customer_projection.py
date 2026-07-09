import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.platform.db.base_class import Base


class CustomerProjection(Base):
    """Copia local (solo lectura) de los datos de Customer que `conversations` necesita
    para enriquecer chats (nombre, teléfono, email, lead_status), mantenida por eventos
    `customer.created/updated/deleted` del módulo `customers`. Sin FK real."""

    __tablename__ = "conversations_customer_projection"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    lead_status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEW")
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
