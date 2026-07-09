import asyncio
import uuid
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.modules.identity.domain.entities.user import User
from app.modules.identity.interfaces.api.dependencies.auth_bearer import get_current_user
from app.platform.exceptions import AppException
from app.platform.db.mongo_client import mongo_client

# Gateways
from app.modules.reporting.infrastructure.gateways.tenants_gateway import TenantsGateway
from app.modules.reporting.infrastructure.gateways.customers_gateway import CustomersGateway
from app.modules.reporting.infrastructure.gateways.scheduling_gateway import SchedulingGateway
from app.modules.reporting.infrastructure.gateways.identity_gateway import IdentityGateway

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_security = HTTPBearer()


async def get_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(_security)) -> str:
    return credentials.credentials


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
ACTIVE_PIPELINE_STAGES = {"NEW", "CONTACTED", "PROPOSAL"}
APPOINTMENT_STATUSES = {"PENDING", "CONFIRMED", "COMPLETED", "CANCELLED", "NO_SHOW"}


# --- Modelos del Negocio Ligeros (Pydantic) ---

class TenantModel(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    phone_number_id: str | None = None
    timezone: str = "America/Mexico_City"
    locale: str = "es"
    mode: str = "SERVICES"
    account_type: str = "INDIVIDUAL"
    enabled_modules: list[str] | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CustomerModel(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    phone: str
    email: str | None = None
    lead_status: str = "NEW"
    pipeline_stage: str = "NEW"
    deal_value: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CustomerNestedModel(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: str | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ServiceNestedModel(BaseModel):
    id: uuid.UUID
    name: str
    duration_minutes: int
    price: float | None = None
    currency: str = "MXN"

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AppointmentModel(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    service_id: uuid.UUID | None = None
    start_at: datetime
    end_at: datetime
    status: str = "PENDING"
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    customer: CustomerNestedModel | None = None
    service: ServiceNestedModel | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UserModel(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    email: str
    role: str = "STAFF"
    is_active: bool = True

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# --- Schemas de Respuesta de la API ---

class KPIModel(BaseModel):
    label: str
    value: str
    delta: str
    direction: str
    is_alert: bool = False


class AppointmentItem(BaseModel):
    id: str
    time: str
    name: str
    detail: str
    status: str
    platform: str


class BotActivityItem(BaseModel):
    id: str
    time: str
    message: str
    status: str


class ReminderItem(BaseModel):
    id: str
    time: str
    name: str
    status: str
    error_message: Optional[str] = None


class PipelineStageSummary(BaseModel):
    stage: str
    count: int
    value: float
    color: str


class FollowupItem(BaseModel):
    id: str
    name: str
    detail: str
    days_inactive: int
    urgency: str
    platform: str


class TeamMemberSummary(BaseModel):
    id: str
    name: str
    role: str
    channel: Optional[str] = None
    appointments_today: Optional[int] = None
    leads_active: Optional[int] = None
    pipeline_value: Optional[float] = None
    followups_due: Optional[int] = None
    messages_today: int = 0
    status: str = "active"


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


# --- Helpers de formato y tiempo ---

def _safe_timezone(tz_name: str | None) -> tzinfo:
    try:
        return ZoneInfo(tz_name or "UTC")
    except Exception:
        if tz_name == "America/Mexico_City":
            return timezone(timedelta(hours=-6), name="America/Mexico_City")
        return timezone.utc


def _at_timezone(value: datetime | None, tz: tzinfo) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def _mongo_datetime(value: datetime) -> datetime:
    return value.replace(tzinfo=None)


def _format_clock(value: datetime | None, tz: tzinfo) -> str:
    localized = _at_timezone(value, tz)
    if not localized:
        return "--:--"
    return localized.strftime("%H:%M")


def _format_money(value: float | int | None) -> str:
    amount = float(value or 0)
    return f"${amount:,.0f}"


def _format_percent(value: float) -> str:
    return f"{value:.1f}%"


def _comparison_delta(current: int, previous: int, suffix: str = "vs ayer") -> tuple[str, str]:
    diff = current - previous
    if diff > 0:
        return f"+{diff} {suffix}", "up"
    if diff < 0:
        return f"{abs(diff)} menos {suffix}", "down"
    return f"sin cambios {suffix}", "neutral"


def _relative_time(value: datetime | None, now: datetime, tz: tzinfo) -> str:
    localized = _at_timezone(value, tz)
    if not localized:
        return "Sin fecha"

    delta = max(now - localized, timedelta())
    if delta < timedelta(minutes=1):
        return "Ahora"

    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        unit = "min" if minutes == 1 else "mins"
        return f"Hace {minutes} {unit}"

    hours = minutes // 60
    if hours < 24:
        unit = "hora" if hours == 1 else "horas"
        return f"Hace {hours} {unit}"

    days = hours // 24
    unit = "dia" if days == 1 else "dias"
    return f"Hace {days} {unit}"


def _normalise_platform(value: Any) -> str:
    platform = str(value or "whatsapp").lower()
    if "instagram" in platform:
        return "instagram"
    return "whatsapp"


def _message_preview(value: Any, max_length: int = 60) -> str:
    content = str(value or "").strip()
    if not content:
        return "Mensaje sin texto"
    if len(content) <= max_length:
        return content
    return f"{content[: max_length - 1]}..."


def _customer_created_between(customer: CustomerModel, start: datetime, end: datetime, tz: tzinfo) -> bool:
    created_at = _at_timezone(customer.created_at, tz)
    return bool(created_at and start <= created_at < end)


def _customer_updated_days(customer: CustomerModel, now: datetime, tz: tzinfo) -> int:
    updated_at = _at_timezone(customer.updated_at or customer.created_at, tz)
    if not updated_at:
        return 0
    return max((now.date() - updated_at.date()).days, 0)


# --- Integración MongoDB (Chats) ---

async def _load_chat_metrics(
    tenant_id: Any,
    customers_by_id: dict[str, CustomerModel],
    start_today: datetime,
    end_today: datetime,
    start_yesterday: datetime,
    end_yesterday: datetime,
    now: datetime,
    tz: tzinfo,
) -> dict[str, Any]:
    empty = {
        "platform_by_customer_id": {},
        "messages_today": 0,
        "inbound_today": 0,
        "messages_yesterday": 0,
        "recent_activity": [],
    }
    if mongo_client.db is None:
        return empty

    try:
        db_mongo = mongo_client.db
        raw_chats = await db_mongo.history_chats.find({"tenantId": str(tenant_id)}).to_list(length=500)
        chat_ids = [str(chat.get("_id")) for chat in raw_chats if chat.get("_id")]
        customer_by_chat_id = {
            str(chat.get("_id")): str(chat.get("customerId"))
            for chat in raw_chats
            if chat.get("_id") and chat.get("customerId")
        }
        platform_by_customer_id = {
            str(chat.get("customerId")): _normalise_platform(chat.get("platform"))
            for chat in raw_chats
            if chat.get("customerId")
        }

        if not chat_ids:
            return {**empty, "platform_by_customer_id": platform_by_customer_id}

        today_filter = {
            "historyChatId": {"$in": chat_ids},
            "sentAt": {"$gte": _mongo_datetime(start_today), "$lt": _mongo_datetime(end_today)},
        }
        yesterday_filter = {
            "historyChatId": {"$in": chat_ids},
            "sentAt": {"$gte": _mongo_datetime(start_yesterday), "$lt": _mongo_datetime(end_yesterday)},
        }

        messages_today = await db_mongo.messages.count_documents(today_filter)
        inbound_today = await db_mongo.messages.count_documents({**today_filter, "direction": "INBOUND"})
        messages_yesterday = await db_mongo.messages.count_documents(yesterday_filter)

        recent_docs = await (
            db_mongo.messages.find({"historyChatId": {"$in": chat_ids}})
            .sort("sentAt", -1)
            .limit(6)
            .to_list(length=6)
        )

        recent_activity = []
        for msg in recent_docs:
            chat_id = str(msg.get("historyChatId"))
            customer_id = customer_by_chat_id.get(chat_id)
            customer = customers_by_id.get(customer_id or "")
            customer_name = customer.name if customer else "Cliente"
            direction = str(msg.get("direction") or "").upper()
            prefix = "Mensaje entrante de" if direction == "INBOUND" else "Mensaje enviado a"
            status = "warning" if str(msg.get("status") or "").upper() == "FAILED" else "info"
            recent_activity.append(
                BotActivityItem(
                    id=str(msg.get("_id")),
                    time=_relative_time(msg.get("sentAt"), now, tz),
                    message=f"{prefix} {customer_name}: {_message_preview(msg.get('content'))}",
                    status=status,
                )
            )

        return {
            "platform_by_customer_id": platform_by_customer_id,
            "messages_today": messages_today,
            "inbound_today": inbound_today,
            "messages_yesterday": messages_yesterday,
            "recent_activity": recent_activity,
        }
    except Exception:
        return empty


# --- Helpers de construcción de Métricas ---

def _build_pipeline_summary(customers: list[CustomerModel]) -> list[PipelineStageSummary]:
    stage_counts = {stage: 0 for stage in PIPELINE_STAGE_LABELS}
    stage_values = {stage: 0.0 for stage in PIPELINE_STAGE_LABELS}

    for customer in customers:
        stage = customer.pipeline_stage if customer.pipeline_stage in PIPELINE_STAGE_LABELS else "NEW"
        stage_counts[stage] += 1
        stage_values[stage] += float(customer.deal_value or 0)

    return [
        PipelineStageSummary(
            stage=PIPELINE_STAGE_LABELS[stage],
            count=stage_counts[stage],
            value=stage_values[stage],
            color=PIPELINE_STAGE_COLORS[stage],
        )
        for stage in PIPELINE_STAGE_LABELS
    ]


def _build_followups(
    customers: list[CustomerModel],
    platform_by_customer_id: dict[str, str],
    now: datetime,
    tz: tzinfo,
) -> list[FollowupItem]:
    followups = []
    details_by_stage = {
        "NEW": "Contactar y calificar lead",
        "CONTACTED": "Dar seguimiento al primer contacto",
        "PROPOSAL": "Revisar propuesta y siguiente paso",
    }

    for customer in customers:
        stage = customer.pipeline_stage if customer.pipeline_stage in PIPELINE_STAGE_LABELS else "NEW"
        if stage not in ACTIVE_PIPELINE_STAGES or customer.lead_status == "BLOCKED":
            continue

        days_inactive = _customer_updated_days(customer, now, tz)
        if days_inactive < 2:
            continue

        urgency = "hot" if days_inactive >= 4 else "warm"
        followups.append(
            FollowupItem(
                id=str(customer.id),
                name=customer.name,
                detail=details_by_stage.get(stage, "Dar seguimiento"),
                days_inactive=days_inactive,
                urgency=urgency,
                platform=platform_by_customer_id.get(str(customer.id), "whatsapp"),
            )
        )

    followups.sort(key=lambda item: (item.urgency != "hot", -item.days_inactive, item.name.lower()))
    return followups[:10]


def _build_activity_from_customers(
    customers: list[CustomerModel],
    now: datetime,
    tz: tzinfo,
    limit: int = 4,
) -> list[BotActivityItem]:
    recent_customers = sorted(
        customers,
        key=lambda customer: _at_timezone(customer.created_at, tz) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    activity = []
    for customer in recent_customers[:limit]:
        activity.append(
            BotActivityItem(
                id=f"customer-{customer.id}",
                time=_relative_time(customer.created_at, now, tz),
                message=f"Nuevo cliente registrado: {customer.name}",
                status="success",
            )
        )
    return activity


def _build_activity_from_appointments(
    appointments: list[tuple[AppointmentModel, CustomerNestedModel | None, ServiceNestedModel | None]],
    now: datetime,
    tz: tzinfo,
    limit: int = 4,
) -> list[BotActivityItem]:
    recent = sorted(
        appointments,
        key=lambda row: _at_timezone(row[0].created_at, tz) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    activity = []
    for appointment, customer, service in recent[:limit]:
        service_name = service.name if service else "cita"
        customer_name = customer.name if customer else "Cliente"
        activity.append(
            BotActivityItem(
                id=f"appointment-{appointment.id}",
                time=_relative_time(appointment.created_at, now, tz),
                message=f"Cita registrada para {customer_name}: {service_name}",
                status="success" if appointment.status != "CANCELLED" else "warning",
            )
        )
    return activity


def _build_team_summary(
    users: list[UserModel],
    account_type: str,
    mode: str,
    aggregate_metrics: dict[str, Any],
) -> list[TeamMemberSummary] | None:
    if account_type not in ("BUSINESS", "TEAM"):
        return None
    if not users:
        return None

    show_aggregate_metrics = len(users) == 1
    members = []
    for user in users:
        common = {
            "id": str(user.id),
            "name": user.name,
            "channel": user.email if account_type == "TEAM" else None,
            "messages_today": int(aggregate_metrics.get("messages_today", 0)) if show_aggregate_metrics else 0,
            "status": "active" if user.is_active else "idle",
        }

        if mode == "SERVICES":
            members.append(
                TeamMemberSummary(
                    **common,
                    role="AGENT",
                    appointments_today=int(aggregate_metrics.get("appointments_today", 0))
                    if show_aggregate_metrics
                    else 0,
                    followups_due=int(aggregate_metrics.get("reminders_pending", 0))
                    if show_aggregate_metrics
                    else 0,
                )
            )
        else:
            members.append(
                TeamMemberSummary(
                    **common,
                    role="REP",
                    leads_active=int(aggregate_metrics.get("leads_active", 0)) if show_aggregate_metrics else 0,
                    pipeline_value=float(aggregate_metrics.get("pipeline_value", 0)) if show_aggregate_metrics else 0,
                    followups_due=int(aggregate_metrics.get("followups_due", 0)) if show_aggregate_metrics else 0,
                )
            )

    return members


# --- Endpoint Principal /stats ---

@router.get("/stats")
async def get_dashboard_stats(
    mode: Optional[str] = None,
    account_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(_security),
):
    try:
        # Obtener token de acceso
        token = credentials.credentials

        # Instanciar Gateways
        tenants_gateway = TenantsGateway(token)
        customers_gateway = CustomersGateway(token)
        scheduling_gateway = SchedulingGateway(token)
        identity_gateway = IdentityGateway(token)

        # 1. Cargar configuración de Tenant
        tenant_data = await tenants_gateway.get_tenant(current_user.tenant_id)
        if not tenant_data:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        tenant = TenantModel.model_validate(tenant_data)

        active_mode = (mode or tenant.mode or "SERVICES").upper()
        active_account_type = (account_type or tenant.account_type or "INDIVIDUAL").upper()
        tenant_tz = _safe_timezone(tenant.timezone)

        # Configurar rangos de fechas locales al huso horario del Tenant
        now = datetime.now(tenant_tz)
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_today = start_today + timedelta(days=1)
        start_yesterday = start_today - timedelta(days=1)
        end_yesterday = start_today
        next_24h = now + timedelta(hours=24)
        start_week = start_today - timedelta(days=7)

        # 2. Consultar servicios externos de forma asíncrona y paralela
        customers_raw, appointments_raw, users_raw = await asyncio.gather(
            customers_gateway.list_customers(),
            scheduling_gateway.list_appointments(start_yesterday, next_24h),
            identity_gateway.list_users()
        )

        # Parsear a Modelos Ligeros
        customers = [CustomerModel.model_validate(c) for c in customers_raw]
        customers_by_id = {str(c.id): c for c in customers}
        
        all_appointments = [AppointmentModel.model_validate(a) for a in appointments_raw]
        users = [UserModel.model_validate(u) for u in users_raw]

        # 3. Cargar métricas de chats desde MongoDB
        chat_metrics = await _load_chat_metrics(
            current_user.tenant_id,
            customers_by_id,
            start_today,
            end_today,
            start_yesterday,
            end_yesterday,
            now,
            tenant_tz,
        )

        # Transformar citas a estructura esperada (appointment, customer, service)
        appointments_today = []
        for appt in all_appointments:
            if start_today <= appt.start_at < end_today:
                appointments_today.append((appt, appt.customer, appt.service))

        # --- Modo Servicios ---
        if active_mode == "SERVICES":
            appointments_today_count = len(appointments_today)
            
            # Citas de ayer
            appointments_yesterday_count = sum(
                1
                for appt in all_appointments
                if start_yesterday <= appt.start_at < end_yesterday
            )
            
            # Citas próximas 24h (pendientes o confirmadas)
            upcoming_count = sum(
                1
                for appt in all_appointments
                if now <= appt.start_at < next_24h and appt.status in {"PENDING", "CONFIRMED"}
            )

            appt_delta, appt_direction = _comparison_delta(
                appointments_today_count,
                appointments_yesterday_count,
            )
            message_delta, message_direction = _comparison_delta(
                int(chat_metrics["messages_today"]),
                int(chat_metrics["messages_yesterday"]),
            )

            new_customers_today = sum(
                1
                for customer in customers
                if _customer_created_between(customer, start_today, end_today, tenant_tz)
            )

            appointment_items = [
                AppointmentItem(
                    id=str(appointment.id),
                    time=_format_clock(appointment.start_at, tenant_tz),
                    name=customer.name if customer else "Cliente",
                    detail=service.name if service else (appointment.notes or "Sin servicio"),
                    status=appointment.status if appointment.status in APPOINTMENT_STATUSES else "PENDING",
                    platform=chat_metrics["platform_by_customer_id"].get(str(appointment.customer_id), "whatsapp"),
                )
                for appointment, customer, service in appointments_today
            ]

            reminder_candidates = [
                row
                for row in appointments_today
                if row[0].status in {"PENDING", "CONFIRMED"}
                and (_at_timezone(row[0].start_at, tenant_tz) or now) >= now
            ]
            reminders = [
                ReminderItem(
                    id=str(appointment.id),
                    time=_format_clock(appointment.start_at, tenant_tz),
                    name=customer.name if customer else "Cliente",
                    status="pending",
                )
                for appointment, customer, _service in reminder_candidates[:10]
            ]

            bot_activity = list(chat_metrics["recent_activity"])
            if len(bot_activity) < 6:
                bot_activity.extend(
                    _build_activity_from_appointments(
                        appointments_today,
                        now,
                        tenant_tz,
                        limit=6 - len(bot_activity),
                    )
                )
            if len(bot_activity) < 6:
                bot_activity.extend(
                    _build_activity_from_customers(
                        customers,
                        now,
                        tenant_tz,
                        limit=6 - len(bot_activity),
                    )
                )

            kpis = [
                KPIModel(
                    label="Citas hoy",
                    value=str(appointments_today_count),
                    delta=appt_delta,
                    direction=appt_direction,
                ),
                KPIModel(
                    label="Mensajes hoy",
                    value=str(chat_metrics["messages_today"]),
                    delta=message_delta,
                    direction=message_direction,
                ),
                KPIModel(
                    label="Recordatorios pendientes",
                    value=str(len(reminders)),
                    delta=f"{upcoming_count} citas prox. 24h",
                    direction="neutral",
                    is_alert=False,
                ),
                KPIModel(
                    label="Clientes",
                    value=str(len(customers)),
                    delta=f"{new_customers_today} nuevos hoy",
                    direction="up" if new_customers_today else "neutral",
                ),
            ]

            team_summary = _build_team_summary(
                users,
                active_account_type,
                "SERVICES",
                {
                    "appointments_today": appointments_today_count,
                    "messages_today": chat_metrics["messages_today"],
                    "reminders_pending": len(reminders),
                },
            )

            return DashboardServicesResponse(
                mode="SERVICES",
                kpis=kpis,
                appointments=appointment_items,
                bot_activity=bot_activity[:6],
                reminders=reminders,
                has_failed_reminders=False,
                team_summary=team_summary,
            )

        # --- Modo Ventas ---
        pipeline_summary = _build_pipeline_summary(customers)
        followups = _build_followups(
            customers,
            chat_metrics["platform_by_customer_id"],
            now,
            tenant_tz,
        )
        active_customers = [
            customer
            for customer in customers
            if (customer.pipeline_stage if customer.pipeline_stage in PIPELINE_STAGE_LABELS else "NEW")
            in ACTIVE_PIPELINE_STAGES
            and customer.lead_status != "BLOCKED"
        ]
        active_leads_count = len(active_customers)
        pipeline_value = sum(float(customer.deal_value or 0) for customer in active_customers)
        new_leads_week = sum(
            1
            for customer in customers
            if _customer_created_between(customer, start_week, end_today, tenant_tz)
        )
        won_count = sum(1 for customer in customers if customer.pipeline_stage == "WON")
        lost_count = sum(1 for customer in customers if customer.pipeline_stage == "LOST")
        closed_count = won_count + lost_count
        close_rate = (won_count / closed_count * 100) if closed_count else 0
        proposal_count = sum(1 for customer in customers if customer.pipeline_stage == "PROPOSAL")
        hot_followups = sum(1 for followup in followups if followup.urgency == "hot")

        bot_activity = list(chat_metrics["recent_activity"])
        if len(bot_activity) < 6:
            bot_activity.extend(
                _build_activity_from_customers(
                    customers,
                    now,
                    tenant_tz,
                    limit=6 - len(bot_activity),
                )
            )

        kpis = [
            KPIModel(
                label="Leads activos",
                value=str(active_leads_count),
                delta=f"{new_leads_week} nuevos 7d",
                direction="up" if new_leads_week else "neutral",
            ),
            KPIModel(
                label="Valor del pipeline",
                value=_format_money(pipeline_value),
                delta=f"{proposal_count} en propuesta",
                direction="up" if pipeline_value else "neutral",
            ),
            KPIModel(
                label="Tasa de cierre",
                value=_format_percent(close_rate),
                delta=f"{won_count} ganados / {lost_count} perdidos",
                direction="up" if won_count else "neutral",
            ),
            KPIModel(
                label="Follow-ups hoy",
                value=str(len(followups)),
                delta=f"{hot_followups} calientes",
                direction="down" if followups else "neutral",
                is_alert=bool(followups),
            ),
        ]

        team_summary = _build_team_summary(
            users,
            active_account_type,
            "SALES",
            {
                "messages_today": chat_metrics["messages_today"],
                "leads_active": active_leads_count,
                "pipeline_value": pipeline_value,
                "followups_due": len(followups),
            },
        )

        return DashboardSalesResponse(
            mode="SALES",
            kpis=kpis,
            pipeline_summary=pipeline_summary,
            followups=followups,
            bot_activity=bot_activity[:6],
            team_summary=team_summary,
        )

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
