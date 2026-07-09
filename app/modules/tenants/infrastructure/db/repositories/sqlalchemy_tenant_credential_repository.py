import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tenants.domain.entities.tenant_credential import TenantCredential as DomainCredential
from app.modules.tenants.domain.ports.tenant_credential_repository import TenantCredentialRepository
from app.modules.tenants.infrastructure.db.models.tenant_credential import TenantCredential as DbCredential

class SQLAlchemyTenantCredentialRepository(TenantCredentialRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_cred: DbCredential) -> DomainCredential:
        return DomainCredential(
            id=db_cred.id,
            tenant_id=db_cred.tenant_id,
            credential_type=db_cred.credential_type,
            encrypted_value=db_cred.encrypted_value,
            created_at=db_cred.created_at,
            updated_at=db_cred.updated_at
        )

    def _to_db(self, domain_cred: DomainCredential) -> DbCredential:
        return DbCredential(
            id=domain_cred.id,
            tenant_id=domain_cred.tenant_id,
            credential_type=domain_cred.credential_type,
            encrypted_value=domain_cred.encrypted_value,
            created_at=domain_cred.created_at,
            updated_at=domain_cred.updated_at
        )

    async def save(self, credential: DomainCredential) -> DomainCredential:
        db_cred = await self.session.get(DbCredential, credential.id)
        if db_cred:
            db_cred.encrypted_value = credential.encrypted_value
            db_cred.updated_at = credential.updated_at
        else:
            stmt = select(DbCredential).where(
                DbCredential.tenant_id == credential.tenant_id,
                DbCredential.credential_type == credential.credential_type
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.encrypted_value = credential.encrypted_value
                existing.updated_at = credential.updated_at
                db_cred = existing
            else:
                db_cred = self._to_db(credential)
                self.session.add(db_cred)
        
        await self.session.flush()
        await self.session.refresh(db_cred)
        return self._to_domain(db_cred)

    async def get_by_tenant_and_type(
        self, tenant_id: uuid.UUID, credential_type: str
    ) -> DomainCredential | None:
        stmt = select(DbCredential).where(
            DbCredential.tenant_id == tenant_id,
            DbCredential.credential_type == credential_type
        )
        result = await self.session.execute(stmt)
        db_cred = result.scalar_one_or_none()
        if not db_cred:
            return None
        return self._to_domain(db_cred)

    async def delete(self, tenant_id: uuid.UUID, credential_type: str) -> None:
        stmt = delete(DbCredential).where(
            DbCredential.tenant_id == tenant_id,
            DbCredential.credential_type == credential_type
        )
        await self.session.execute(stmt)
        await self.session.flush()
