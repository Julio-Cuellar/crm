import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.platform.db.base_class import Base


class Tenant(Base):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    phone_number_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="America/Mexico_City")
    locale: Mapped[str] = mapped_column(String(10), default="es")
    mode: Mapped[str] = mapped_column(String(20), default="SERVICES", nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), default="INDIVIDUAL", nullable=False)
    enabled_modules: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_system_prompt: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
