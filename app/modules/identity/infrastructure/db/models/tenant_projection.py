import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.platform.db.base_class import Base


class TenantProjection(Base):
    """Copia local (solo lectura) del nombre de un tenant, mantenida por eventos
    `tenant.created`/`tenant.updated` del módulo `tenants`. `identity` la usa para
    mostrar el nombre del negocio en invitaciones sin llamar al repositorio de otro
    módulo directamente."""

    __tablename__ = "identity_tenant_projection"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
