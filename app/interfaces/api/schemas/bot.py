import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BotReplyContent(BaseModel):
    type: str = "TEXT"
    content: str = ""
    media_url: str | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BotReplySummary(BaseModel):
    text: str
    version: int = 0

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BotReplyMemory(BaseModel):
    # Presente solo cuando la IA recompactó el resumen; si es None se conserva el anterior.
    summary: BotReplySummary | None = None
    # Patch parcial sobre el estado estructurado del flujo.
    state_patch: dict = Field(default_factory=dict)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BotReplyRequest(BaseModel):
    """Cuerpo del callback que n8n envía a POST /bridge/n8n/reply."""

    correlation_id: str
    tenant_id: uuid.UUID
    chat_id: uuid.UUID
    customer_id: uuid.UUID
    channel: str = "WHATSAPP"
    reply: BotReplyContent
    memory: BotReplyMemory = Field(default_factory=BotReplyMemory)
    handoff: bool = False
    actions: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
