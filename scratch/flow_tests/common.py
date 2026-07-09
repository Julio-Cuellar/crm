import asyncio
import json
import urllib.request
import urllib.error
from app.platform.db.session import async_session_factory
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_pending_registration_repository import SQLAlchemyPendingRegistrationRepository
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_invitation_repository import SQLAlchemyInvitationRepository
from app.modules.identity.infrastructure.db.models.invitation import Invitation as DbInvitation
from sqlalchemy import select

API_BASE = "http://127.0.0.1:8000/api/v1"


def make_request(url, data=None, method="GET", headers=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
            
    if data:
        json_data = json.dumps(data).encode("utf-8")
        req.data = json_data
        
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            return status_code, json.loads(body)
    except urllib.error.HTTPError as e:
        status_code = e.code
        body = e.read().decode("utf-8")
        try:
            return status_code, json.loads(body)
        except json.JSONDecodeError:
            return status_code, body
    except Exception as e:
        return 0, str(e)


async def get_verification_token(email: str) -> str | None:
    # Reintentos con delay para asegurar sincronía de transacción
    for _ in range(5):
        async with async_session_factory() as session:
            repo = SQLAlchemyPendingRegistrationRepository(session)
            pending = await repo.get_by_email(email)
            if pending and pending.verification_token:
                return pending.verification_token
        await asyncio.sleep(0.2)
    return None


async def get_invitation_token(email: str) -> str | None:
    # Reintentos con delay para asegurar sincronía de transacción
    for _ in range(5):
        async with async_session_factory() as session:
            stmt = select(DbInvitation).where(DbInvitation.email == email)
            result = await session.execute(stmt)
            db_invite = result.scalar_one_or_none()
            if db_invite and db_invite.token:
                return db_invite.token
        await asyncio.sleep(0.2)
    return None
