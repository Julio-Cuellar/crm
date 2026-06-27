from fastapi import APIRouter, Depends, HTTPException, status
from app.interfaces.api.dependencies.auth_bearer import get_current_user
from app.domain.entities.user import User
from app.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.interfaces.api.dependencies.tenants import get_tenant_repository
from app.domain.exceptions.base import AppException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Esquemas de Pydantic para el Dashboard
class KPIModel(BaseModel):
    label: str
    value: str
    delta: str
    direction: str  # "up", "down", "neutral"
    is_alert: bool = False

# Esquemas para Modo Servicios
class AppointmentItem(BaseModel):
    id: str
    time: str
    name: str
    detail: str
    status: str  # "PENDING", "CONFIRMED", "COMPLETED", "CANCELLED", "NO_SHOW"
    platform: str  # "whatsapp", "instagram"

class BotActivityItem(BaseModel):
    id: str
    time: str
    message: str
    status: str  # "success", "warning", "info"

class ReminderItem(BaseModel):
    id: str
    time: str
    name: str
    status: str  # "sent", "failed", "pending"
    error_message: Optional[str] = None

class DashboardServicesResponse(BaseModel):
    mode: str = "SERVICES"
    kpis: List[KPIModel]
    appointments: List[AppointmentItem]
    bot_activity: List[BotActivityItem]
    reminders: List[ReminderItem]
    has_failed_reminders: bool

# Esquemas para Modo Ventas
class PipelineStageSummary(BaseModel):
    stage: str  # "Nuevo", "Contactado", "Propuesta", "Ganado", "Perdido"
    count: int
    value: float
    color: str

class FollowupItem(BaseModel):
    id: str
    name: str
    detail: str
    days_inactive: int
    urgency: str  # "ok", "warm", "hot"
    platform: str  # "whatsapp", "instagram"

class DashboardSalesResponse(BaseModel):
    mode: str = "SALES"
    kpis: List[KPIModel]
    pipeline_summary: List[PipelineStageSummary]
    followups: List[FollowupItem]
    bot_activity: List[BotActivityItem]


@router.get("/stats")
async def get_dashboard_stats(
    mode: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    tenant_repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository)
):
    """
    Retorna las estadísticas unificadas del dashboard principal basadas en el modo de operación del tenant.
    Permite especificar un modo de simulación mediante el parámetro de consulta.
    """
    try:
        tenant = await tenant_repo.get_by_id(current_user.tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        # Usar el modo del query param si viene especificado, sino usar el del tenant
        active_mode = mode.upper() if mode else tenant.mode

        if active_mode == "SERVICES":
            kpis = [
                KPIModel(label="Citas hoy", value="14", delta="+12% vs ayer", direction="up"),
                KPIModel(label="Mensajes nuevos", value="28", delta="+5 sin leer", direction="neutral"),
                KPIModel(label="Recordatorios hoy", value="42", delta="2 fallidos", direction="down", is_alert=True),
                KPIModel(label="Bot hoy", value="108", delta="8 citas creadas", direction="up")
            ]

            appointments = [
                AppointmentItem(id="1", time="09:00", name="Dra. Ana López", detail="Consulta General", status="COMPLETED", platform="whatsapp"),
                AppointmentItem(id="2", time="10:30", name="Carlos Mendoza", detail="Tratamiento de Conducta", status="CONFIRMED", platform="whatsapp"),
                AppointmentItem(id="3", time="11:45", name="María Rodríguez", detail="Limpieza Dental", status="PENDING", platform="instagram"),
                AppointmentItem(id="4", time="14:00", name="Juan Gómez", detail="Consulta Ortodoncia", status="CONFIRMED", platform="whatsapp"),
                AppointmentItem(id="5", time="16:30", name="Sofía Altieri", detail="Extracción", status="CANCELLED", platform="instagram"),
                AppointmentItem(id="6", time="17:00", name="Lucas Beltrán", detail="Blanqueamiento", status="NO_SHOW", platform="whatsapp")
            ]

            bot_activity = [
                BotActivityItem(id="b1", time="Hace 2 min", message="Bot agendó cita a Carlos Mendoza", status="success"),
                BotActivityItem(id="b2", time="Hace 15 min", message="Bot respondió consulta de precios a Lucía Gómez", status="info"),
                BotActivityItem(id="b3", time="Hace 1 hora", message="Alerta: Cliente canceló cita por chat", status="warning"),
                BotActivityItem(id="b4", time="Hace 2 horas", message="Bot creó nuevo cliente: Mateo Silva", status="success")
            ]

            reminders = [
                ReminderItem(id="r1", time="08:00", name="Carlos Mendoza", status="sent"),
                ReminderItem(id="r2", time="08:30", name="María Rodríguez", status="sent"),
                ReminderItem(id="r3", time="09:00", name="Juan Gómez", status="failed", error_message="Error de red de Meta (WABA)"),
                ReminderItem(id="r4", time="10:00", name="Sofía Altieri", status="sent"),
                ReminderItem(id="r5", time="11:00", name="Lucas Beltrán", status="failed", error_message="Número no registrado en WhatsApp")
            ]

            return DashboardServicesResponse(
                mode="SERVICES",
                kpis=kpis,
                appointments=appointments,
                bot_activity=bot_activity,
                reminders=reminders,
                has_failed_reminders=True
            )
        else:
            kpis = [
                KPIModel(label="Leads activos", value="34", delta="+8% esta semana", direction="up"),
                KPIModel(label="Valor del pipeline", value="$45,200", delta="+15% vs mes anterior", direction="up"),
                KPIModel(label="Tasa de cierre", value="24.5%", delta="+2% vs mes anterior", direction="up"),
                KPIModel(label="Follow-ups hoy", value="8", delta="3 vencidos", direction="down", is_alert=True)
            ]

            pipeline_summary = [
                PipelineStageSummary(stage="Nuevo", count=12, value=12000.0, color="#818cf8"),
                PipelineStageSummary(stage="Contactado", count=8, value=16000.0, color="#38bdf8"),
                PipelineStageSummary(stage="Propuesta", count=6, value=17200.0, color="#fb923c"),
                PipelineStageSummary(stage="Ganado", count=5, value=15000.0, color="#4ade80"),
                PipelineStageSummary(stage="Perdido", count=3, value=6000.0, color="#71717a")
            ]

            followups = [
                FollowupItem(id="f1", name="Inmobiliaria Norte", detail="Llamar para propuesta económica", days_inactive=5, urgency="hot", platform="whatsapp"),
                FollowupItem(id="f2", name="Constructora Delta", detail="Enviar catálogo de servicios", days_inactive=3, urgency="warm", platform="whatsapp"),
                FollowupItem(id="f3", name="Estudio Jurídico Ruiz", detail="Confirmar reunión técnica", days_inactive=0, urgency="ok", platform="instagram"),
                FollowupItem(id="f4", name="Clínica del Sol", detail="Responder dudas de integración", days_inactive=4, urgency="hot", platform="whatsapp"),
                FollowupItem(id="f5", name="Distribuidora Sur", detail="Agendar videollamada demo", days_inactive=2, urgency="warm", platform="instagram")
            ]

            bot_activity = [
                BotActivityItem(id="b1", time="Hace 5 min", message="Bot calificó lead: Inmobiliaria Norte (HOT)", status="success"),
                BotActivityItem(id="b2", time="Hace 30 min", message="Bot derivó conversación de Juan Pérez a Humano", status="warning"),
                BotActivityItem(id="b3", time="Hace 3 horas", message="Bot capturó nuevo lead desde Instagram: @martina_estudio", status="success")
            ]

            return DashboardSalesResponse(
                mode="SALES",
                kpis=kpis,
                pipeline_summary=pipeline_summary,
                followups=followups,
                bot_activity=bot_activity
            )

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
