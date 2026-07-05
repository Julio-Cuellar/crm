import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.infrastructure.db.base_class import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    lead_status: Mapped[str] = mapped_column(String(50), default="NEW", nullable=False)  # NEW | CONTACTED | APPOINTMENT_SCHEDULED | APPOINTMENT_CONFIRMED | RECURRING_CLIENT | INACTIVE | BLOCKED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Restricciones e Índices
    __table_args__ = (
        # Asegura que el mismo teléfono no se duplique dentro de un mismo tenant
        UniqueConstraint("tenant_id", "phone", name="uq_customers_tenant_phone"),
        # Acelera la búsqueda de clientes por teléfono al recibir webhooks/mensajes
        Index("idx_customers_tenant_phone", "tenant_id", "phone"),
    )
