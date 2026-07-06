import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.bot_session import BotSession as DomainBotSession
from app.domain.ports.bot_session_repository import BotSessionRepository
from app.infrastructure.db.models.bot_session import BotSession as DbBotSession


class SQLAlchemyBotSessionRepository(BotSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_session: DbBotSession) -> DomainBotSession:
        return DomainBotSession(
            id=db_session.id,
            tenant_id=db_session.tenant_id,
            customer_phone=db_session.customer_phone,
            automation_mode=db_session.automation_mode,
            temp_name=db_session.temp_name,
            temp_email=db_session.temp_email,
            temp_organization=db_session.temp_organization,
            temp_service=db_session.temp_service,
            temp_description=db_session.temp_description,
            temp_appointment_date=db_session.temp_appointment_date,
            temp_folio=db_session.temp_folio,
            context_json=db_session.context_json,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
        )

    def _to_db(self, domain_session: DomainBotSession) -> DbBotSession:
        return DbBotSession(
            id=domain_session.id,
            tenant_id=domain_session.tenant_id,
            customer_phone=domain_session.customer_phone,
            automation_mode=domain_session.automation_mode,
            temp_name=domain_session.temp_name,
            temp_email=domain_session.temp_email,
            temp_organization=domain_session.temp_organization,
            temp_service=domain_session.temp_service,
            temp_description=domain_session.temp_description,
            temp_appointment_date=domain_session.temp_appointment_date,
            temp_folio=domain_session.temp_folio,
            context_json=domain_session.context_json,
            created_at=domain_session.created_at,
            updated_at=domain_session.updated_at,
        )

    async def save(self, session: DomainBotSession) -> DomainBotSession:
        db_session = await self.session.get(DbBotSession, session.id)
        if not db_session:
            stmt = select(DbBotSession).where(DbBotSession.customer_phone == session.customer_phone)
            res = await self.session.execute(stmt)
            db_session = res.scalars().first()

        if db_session:
            db_session.automation_mode = session.automation_mode
            db_session.temp_name = session.temp_name
            db_session.temp_email = session.temp_email
            db_session.temp_organization = session.temp_organization
            db_session.temp_service = session.temp_service
            db_session.temp_description = session.temp_description
            db_session.temp_appointment_date = session.temp_appointment_date
            db_session.temp_folio = session.temp_folio
            db_session.context_json = session.context_json
            db_session.updated_at = session.updated_at
        else:
            db_session = self._to_db(session)
            self.session.add(db_session)

        await self.session.flush()
        await self.session.refresh(db_session)
        return self._to_domain(db_session)

    async def get_by_phone(self, phone: str) -> DomainBotSession | None:
        stmt = select(DbBotSession).where(DbBotSession.customer_phone == phone)
        res = await self.session.execute(stmt)
        db_session = res.scalars().first()
        if not db_session:
            return None
        return self._to_domain(db_session)

    async def get_by_tenant_and_phone(self, tenant_id: uuid.UUID, phone: str) -> DomainBotSession | None:
        stmt = select(DbBotSession).where(
            DbBotSession.tenant_id == tenant_id, DbBotSession.customer_phone == phone
        )
        res = await self.session.execute(stmt)
        db_session = res.scalars().first()
        if not db_session:
            return None
        return self._to_domain(db_session)

    async def delete(self, phone: str) -> bool:
        stmt = select(DbBotSession).where(DbBotSession.customer_phone == phone)
        res = await self.session.execute(stmt)
        db_session = res.scalars().first()
        if not db_session:
            return False
        await self.session.delete(db_session)
        await self.session.flush()
        return True
