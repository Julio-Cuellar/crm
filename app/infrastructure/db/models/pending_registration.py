import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.infrastructure.db.base_class import Base


class PendingRegistration(Base):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tenant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    verification_token: Mapped[str] = mapped_column(String(10), nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
