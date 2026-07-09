# app.platform.db.base
# Importa la clase Base y todos los modelos de todos los módulos, para que
# create_all()/drop_all() los conozca. Único lugar del código con visibilidad
# sobre los modelos de TODOS los módulos — es infraestructura de arranque, no
# lógica de negocio, así que no viola el aislamiento entre módulos.

from app.platform.db.base_class import Base  # noqa: F401
from app.modules.tenants.infrastructure.db.models.tenant import Tenant  # noqa: F401
from app.modules.identity.infrastructure.db.models.user import User  # noqa: F401
from app.modules.identity.infrastructure.db.models.pending_registration import PendingRegistration  # noqa: F401
from app.modules.identity.infrastructure.db.models.invitation import Invitation  # noqa: F401
from app.modules.identity.infrastructure.db.models.blacklisted_token import BlacklistedToken  # noqa: F401
from app.modules.identity.infrastructure.db.models.tenant_projection import TenantProjection  # noqa: F401
from app.modules.catalog.infrastructure.db.models.service import Service  # noqa: F401
from app.modules.customers.infrastructure.db.models.customer import Customer  # noqa: F401
from app.modules.tickets.infrastructure.db.models.ticket import Ticket  # noqa: F401
from app.modules.tenants.infrastructure.db.models.tenant_credential import TenantCredential  # noqa: F401
from app.modules.conversations.infrastructure.db.models.bot_session import BotSession  # noqa: F401
from app.modules.scheduling.infrastructure.db.models.appointment import Appointment  # noqa: F401
from app.modules.scheduling.infrastructure.db.models.customer_projection import CustomerProjection as SchedulingCustomerProjection  # noqa: F401
from app.modules.scheduling.infrastructure.db.models.service_projection import ServiceProjection as SchedulingServiceProjection  # noqa: F401
from app.modules.tickets.infrastructure.db.models.customer_projection import CustomerProjection as TicketsCustomerProjection  # noqa: F401
from app.modules.conversations.infrastructure.db.models.customer_projection import CustomerProjection as ConversationsCustomerProjection  # noqa: F401

