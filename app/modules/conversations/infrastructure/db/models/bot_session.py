import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.platform.db.base_class import Base


class BotSession(Base):
    __tablename__ = "bot_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    automation_mode: Mapped[str] = mapped_column(String(50), default="AUTOMATED", nullable=False)  # AUTOMATED | HUMAN
    context_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Variables temporales para reservas
    temp_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    temp_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    temp_organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    temp_service: Mapped[str | None] = mapped_column(String(200), nullable=True)
    temp_description: Mapped[str | None] = mapped_column(String, nullable=True)
    temp_appointment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    temp_folio: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_bot_sessions_tenant_phone", "tenant_id", "customer_phone"),
    )
