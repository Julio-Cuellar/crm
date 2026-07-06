"""Verifica memoria resumida y payload del bot sin servidor ni Mongo."""
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.use_cases.dispatch_to_bot import DispatchToBotUseCase
from app.domain.ports.bot_gateway import BotGateway
from app.infrastructure.db.repositories.redis_conversation_memory_repository import (
    RedisConversationMemoryRepository,
)


class _FakeTenant:
    id = uuid.uuid4()
    name = "Consultorio Demo"
    mode = "SERVICES"
    locale = "es"
    timezone = "America/Mexico_City"
    ai_system_prompt = None


class _FakeCustomer:
    id = uuid.uuid4()
    name = "Juan Perez"
    phone = "+5215550001111"


class _FakeMongoRepo:
    def __init__(self) -> None:
        self.messages: dict[str, list[dict]] = {}

    async def get_messages_by_chat_id(self, chat_id):
        return self.messages.get(str(chat_id), [])

    async def save_message(self, chat_id, direction, message_type, content, **kwargs):
        msg = {
            "_id": str(uuid.uuid4()),
            "historyChatId": str(chat_id),
            "direction": direction,
            "type": message_type,
            "content": content,
            "sentAt": datetime.now(),
            "status": kwargs.get("status", "SENT"),
        }
        self.messages.setdefault(str(chat_id), []).append(msg)
        return msg


class CapturingGateway(BotGateway):
    def __init__(self):
        self.payloads = []

    async def dispatch(self, payload):
        self.payloads.append(payload)


async def main():
    mongo = _FakeMongoRepo()
    memory = RedisConversationMemoryRepository()
    gateway = CapturingGateway()
    uc = DispatchToBotUseCase(bot_gateway=gateway, memory_repo=memory, mongo_repo=mongo)

    tenant, customer = _FakeTenant(), _FakeCustomer()
    chat = {"_id": uuid.uuid4()}
    chat_id = chat["_id"]

    msgs = ["Hola", "Quiero limpieza", "El jueves 4pm", "Confirmo", "Gracias", "Una duda"]
    for text in msgs:
        await mongo.save_message(chat_id=chat_id, direction="INBOUND", message_type="TEXT", content=text)
        await uc.execute(tenant=tenant, customer=customer, chat=chat, content=text)
        await asyncio.sleep(0.05)

    print("=== PAYLOADS ENVIADOS AL BOT ===")
    for i, payload in enumerate(gateway.payloads, 1):
        ctx = payload["context"]
        print(
            f"turno {i}: msg={payload['message']['content']!r:20} "
            f"refreshSummary={ctx['refreshSummary']!s:5} "
            f"recentTurns={len(ctx['recentTurns'])} "
            f"historyPlano={'history' in ctx}"
        )

    assert "history" not in gateway.payloads[0]["context"]
    assert all(len(p["context"]["recentTurns"]) <= 2 for p in gateway.payloads)

    await memory.save_summary(chat_id, "Juan agenda limpieza jueves 4pm.", version=1)
    await memory.merge_state(chat_id, {"stage": "confirming"})
    snap = await memory.get(chat_id)
    assert snap["summary"]["version"] == 1
    assert snap["state"]["stage"] == "confirming"

    cid = "corr-123"
    assert await memory.mark_processed(cid) is True
    assert await memory.mark_processed(cid) is False

    print("MEMORY CHECK OK")


asyncio.run(main())
