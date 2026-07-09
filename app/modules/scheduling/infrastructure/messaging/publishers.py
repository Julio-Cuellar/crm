from typing import Any

from app.modules.scheduling.domain.entities.appointment import Appointment
from app.platform.messaging.event_bus import EventBus


def _appointment_payload(appointment: Appointment) -> dict[str, Any]:
    return {
        "appointmentId": str(appointment.id),
        "tenantId": str(appointment.tenant_id),
        "customerId": str(appointment.customer_id),
        "serviceId": str(appointment.service_id) if appointment.service_id else None,
        "startAt": appointment.start_at.isoformat(),
        "endAt": appointment.end_at.isoformat(),
        "status": appointment.status,
    }


async def publish_appointment_created(event_bus: EventBus | None, appointment: Appointment) -> None:
    if event_bus:
        await event_bus.publish("appointment.created", _appointment_payload(appointment))


async def publish_appointment_updated(event_bus: EventBus | None, appointment: Appointment) -> None:
    if event_bus:
        await event_bus.publish("appointment.updated", _appointment_payload(appointment))
