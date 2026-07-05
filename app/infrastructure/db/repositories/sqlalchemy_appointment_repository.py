import uuid
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.appointment import Appointment as DomainAppointment
from app.domain.ports.appointment_repository import AppointmentRepository
from app.infrastructure.db.models.appointment import Appointment as DbAppointment


class SQLAlchemyAppointmentRepository(AppointmentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_appt: DbAppointment) -> DomainAppointment:
        return DomainAppointment(
            id=db_appt.id,
            tenant_id=db_appt.tenant_id,
            customer_id=db_appt.customer_id,
            service_id=db_appt.service_id,
            start_at=db_appt.start_at,
            end_at=db_appt.end_at,
            status=db_appt.status,
            notes=db_appt.notes,
            created_at=db_appt.created_at,
            updated_at=db_appt.updated_at,
        )

    def _to_db(self, dom_appt: DomainAppointment) -> DbAppointment:
        return DbAppointment(
            id=dom_appt.id,
            tenant_id=dom_appt.tenant_id,
            customer_id=dom_appt.customer_id,
            service_id=dom_appt.service_id,
            start_at=dom_appt.start_at,
            end_at=dom_appt.end_at,
            status=dom_appt.status,
            notes=dom_appt.notes,
            created_at=dom_appt.created_at,
            updated_at=dom_appt.updated_at,
        )

    async def save(self, appointment: DomainAppointment) -> DomainAppointment:
        db_appt = await self.session.get(DbAppointment, appointment.id)
        if db_appt:
            db_appt.start_at = appointment.start_at
            db_appt.end_at = appointment.end_at
            db_appt.status = appointment.status
            db_appt.notes = appointment.notes
            db_appt.service_id = appointment.service_id
            db_appt.updated_at = appointment.updated_at
        else:
            db_appt = self._to_db(appointment)
            self.session.add(db_appt)
        await self.session.flush()
        return self._to_domain(db_appt)

    async def get_by_id(self, appointment_id: uuid.UUID) -> DomainAppointment | None:
        db_appt = await self.session.get(DbAppointment, appointment_id)
        if not db_appt:
            return None
        return self._to_domain(db_appt)

    async def get_latest_by_customer(self, customer_id: uuid.UUID) -> DomainAppointment | None:
        stmt = (
            select(DbAppointment)
            .where(DbAppointment.customer_id == customer_id)
            .order_by(DbAppointment.start_at.desc())
        )
        res = await self.session.execute(stmt)
        db_appt = res.scalars().first()
        if not db_appt:
            return None
        return self._to_domain(db_appt)

    async def list_by_tenant_and_range(
        self, tenant_id: uuid.UUID, start_range: datetime, end_range: datetime
    ) -> list[DomainAppointment]:
        stmt = (
            select(DbAppointment)
            .where(
                and_(
                    DbAppointment.tenant_id == tenant_id,
                    DbAppointment.start_at >= start_range,
                    DbAppointment.start_at <= end_range,
                )
            )
            .order_by(DbAppointment.start_at.asc())
        )
        res = await self.session.execute(stmt)
        db_appts = res.scalars().all()
        return [self._to_domain(a) for a in db_appts]

    async def delete(self, appointment_id: uuid.UUID) -> bool:
        db_appt = await self.session.get(DbAppointment, appointment_id)
        if not db_appt:
            return False
        await self.session.delete(db_appt)
        await self.session.flush()
        return True
