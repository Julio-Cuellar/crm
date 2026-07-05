from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.interfaces.api.dependencies.auth_bearer import get_current_user
from app.domain.entities.user import User
from app.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.infrastructure.db.session import get_db
from app.interfaces.api.dependencies.tenants import get_tenant_repository
from app.domain.exceptions.base import AppException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

PIPELINE_STAGE_LABELS = {
    "NEW": "Nuevo",
    "CONTACTED": "Contactado",
    "PROPOSAL": "Propuesta",
    "WON": "Ganado",
    "LOST": "Perdido",
}
PIPELINE_STAGE_COLORS = {
    "NEW": "#818cf8",
    "CONTACTED": "#38bdf8",
    "PROPOSAL": "#fb923c",
    "WON": "#4ade80",
    "LOST": "#71717a",
}

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

class TeamMemberSummary(BaseModel):
    id: str
    name: str
    role: str  # "AGENT" | "REP"
    channel: Optional[str] = None
    appointments_today: Optional[int] = None
    leads_active: Optional[int] = None
    pipeline_value: Optional[float] = None
    followups_due: Optional[int] = None
    messages_today: int = 0
    status: str = "active"  # "active" | "idle"

class DashboardServicesResponse(BaseModel):
    mode: str = "SERVICES"
    kpis: List[KPIModel]
    appointments: List[AppointmentItem]
    bot_activity: List[BotActivityItem]
    reminders: List[ReminderItem]
    has_failed_reminders: bool
    team_summary: Optional[List[TeamMemberSummary]] = None

class DashboardSalesResponse(BaseModel):
    mode: str = "SALES"
    kpis: List[KPIModel]
    pipeline_summary: List[PipelineStageSummary]
    followups: List[FollowupItem]
    bot_activity: List[BotActivityItem]
    team_summary: Optional[List[TeamMemberSummary]] = None


@router.get("/stats")
async def get_dashboard_stats(
    mode: Optional[str] = None,
    account_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    tenant_repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna las estadísticas unificadas del dashboard principal basadas en el modo de operación del tenant.
    Permite especificar un modo de simulación mediante el parámetro de consulta.
    """
    try:
        tenant = await tenant_repo.get_by_id(current_user.tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        # Usar los params del query si vienen, sino los del tenant
        active_mode = mode.upper() if mode else tenant.mode
        active_account_type = account_type.upper() if account_type else tenant.account_type

        # Datos de equipo para BUSINESS y TEAM
        team_summary = None
        if active_account_type in ("BUSINESS", "TEAM") and active_mode == "SERVICES":
            team_summary = [
                TeamMemberSummary(id="a1", name="Laura Suárez", role="AGENT", appointments_today=6, messages_today=22, followups_due=0, status="active"),
                TeamMemberSummary(id="a2", name="Dr. García", role="AGENT", appointments_today=8, messages_today=15, followups_due=1, status="active"),
                TeamMemberSummary(id="a3", name="Recepción", role="AGENT", appointments_today=4, messages_today=31, followups_due=0, status="idle"),
            ]
        elif active_account_type in ("BUSINESS", "TEAM") and active_mode == "SALES":
            channel_prefix = "+54 9 11" if active_account_type == "TEAM" else None
            team_summary = [
                TeamMemberSummary(id="r1", name="Carlos Méndez", role="REP", channel=f"{channel_prefix} 4567-8901" if channel_prefix else None, leads_active=8, pipeline_value=14500.0, followups_due=2, messages_today=12, status="active"),
                TeamMemberSummary(id="r2", name="Ana Prieto", role="REP", channel=f"{channel_prefix} 2345-6789" if channel_prefix else None, leads_active=5, pipeline_value=9800.0, followups_due=0, messages_today=7, status="active"),
                TeamMemberSummary(id="r3", name="Lucas Torres", role="REP", channel=f"{channel_prefix} 8765-4321" if channel_prefix else None, leads_active=12, pipeline_value=22100.0, followups_due=3, messages_today=18, status="active"),
            ]

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
                has_failed_reminders=True,
                team_summary=team_summary
            )
        else:
            kpis = [
                KPIModel(label="Leads activos", value="34", delta="+8% esta semana", direction="up"),
                KPIModel(label="Valor del pipeline", value="$45,200", delta="+15% vs mes anterior", direction="up"),
                KPIModel(label="Tasa de cierre", value="24.5%", delta="+2% vs mes anterior", direction="up"),
                KPIModel(label="Follow-ups hoy", value="8", delta="3 vencidos", direction="down", is_alert=True)
            ]

            customer_repo = SQLAlchemyCustomerRepository(db)
            customers = await customer_repo.get_by_tenant(current_user.tenant_id)

            stage_counts = {stage: 0 for stage in PIPELINE_STAGE_LABELS}
            stage_values = {stage: 0.0 for stage in PIPELINE_STAGE_LABELS}
            for customer in customers:
                stage = customer.pipeline_stage if customer.pipeline_stage in PIPELINE_STAGE_LABELS else "NEW"
                stage_counts[stage] += 1
                stage_values[stage] += customer.deal_value or 0.0

            pipeline_summary = [
                PipelineStageSummary(
                    stage=PIPELINE_STAGE_LABELS[stage],
                    count=stage_counts[stage],
                    value=stage_values[stage],
                    color=PIPELINE_STAGE_COLORS[stage]
                )
                for stage in PIPELINE_STAGE_LABELS
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
                bot_activity=bot_activity,
                team_summary=team_summary
            )

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
