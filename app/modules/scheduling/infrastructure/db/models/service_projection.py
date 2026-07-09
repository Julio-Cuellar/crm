import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.platform.db.base_class import Base


class ServiceProjection(Base):
    """Copia local (solo lectura) de los datos de Service que `scheduling` necesita,
    mantenida por eventos `service.created/updated/deleted` del módulo `catalog`."""

    __tablename__ = "scheduling_service_projection"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(default=60, nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="MXN", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
