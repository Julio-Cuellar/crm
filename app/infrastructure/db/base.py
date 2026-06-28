# app.infrastructure.db.base
# Importa la clase Base y todos los modelos para inicializaciones y migraciones

from app.infrastructure.db.base_class import Base  # noqa: F401
from app.infrastructure.db.models.tenant import Tenant  # noqa: F401
from app.infrastructure.db.models.user import User  # noqa: F401
from app.infrastructure.db.models.pending_registration import PendingRegistration  # noqa: F401
from app.infrastructure.db.models.invitation import Invitation  # noqa: F401
from app.infrastructure.db.models.blacklisted_token import BlacklistedToken  # noqa: F401
from app.infrastructure.db.models.service import Service  # noqa: F401
from app.infrastructure.db.models.customer import Customer  # noqa: F401
from app.infrastructure.db.models.ticket import Ticket  # noqa: F401
from app.infrastructure.db.models.tenant_credential import TenantCredential  # noqa: F401
