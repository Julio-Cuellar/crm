import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.platform.config import settings
from app.legacy.assistant.domain.ports.conversation_memory_repository import ConversationMemoryRepository
from app.modules.conversations.infrastructure.db.mongo.mongo_client import mongo_client

try:
    from redis import asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None


_MEMORY_TTL = 60 * 60 * 24 * 30  # 30 días de memoria caliente
_PROCESSED_TTL = 60 * 15         # 15 min de idempotencia de callback


class _RedisConnection:
    """Cliente Redis perezoso con degradación a memoria local (patrón del mock de Mongo).

    Si el paquete redis no está o el servidor no responde, se cae a un dict en
    proceso. Así el loop del bot funciona en desarrollo sin depender de Redis.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._checked = False
        self._store: dict[str, str] = {}

    async def _c(self) -> Any:
        if self._checked:
            return self._client
        self._checked = True
        if aioredis is None:
            print("[Redis Warning] Paquete redis no disponible; usando memoria local.")
            self._client = None
            return None
        try:
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await client.ping()
            self._client = client
            print("[Redis] Conexión establecida para memoria conversacional.")
        except Exception as e:
            print(f"[Redis Warning] No se pudo conectar a Redis: {e}. Usando memoria local.")
            self._client = None
        return self._client

    async def get(self, key: str) -> str | None:
        client = await self._c()
        if client is None:
            return self._store.get(key)
        return await client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        client = await self._c()
        if client is None:
            self._store[key] = value
            return
        await client.set(key, value, ex=ttl)

    async def incr(self, key: str, ttl: int | None = None) -> int:
        client = await self._c()
        if client is None:
            value = int(self._store.get(key, "0")) + 1
            self._store[key] = str(value)
            return value
        value = await client.incr(key)
        if ttl and value == 1:
            await client.expire(key, ttl)
        return value

    async def setnx(self, key: str, value: str, ttl: int | None = None) -> bool:
        client = await self._c()
        if client is None:
            if key in self._store:
                return False
            self._store[key] = value
            return True
        return bool(await client.set(key, value, ex=ttl, nx=True))


# Singleton a nivel de módulo (una sola conexión Redis por proceso).
_redis_conn = _RedisConnection()


class RedisConversationMemoryRepository(ConversationMemoryRepository):
    def __init__(self) -> None:
        self._r = _redis_conn

    # --- claves ---
    def _k_summary(self, chat_id: uuid.UUID) -> str:
        return f"chat:{chat_id}:summary"

    def _k_state(self, chat_id: uuid.UUID) -> str:
        return f"chat:{chat_id}:state"

    def _k_turns(self, chat_id: uuid.UUID) -> str:
        return f"chat:{chat_id}:turns"

    def _k_base(self, chat_id: uuid.UUID) -> str:
        return f"chat:{chat_id}:turns_base"

    def _k_processed(self, correlation_id: str) -> str:
        return f"bot:reply:{correlation_id}"

    # --- helpers ---
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _empty_summary() -> dict[str, Any]:
        return {"text": "", "version": 0, "updatedAt": None, "turnsSinceRefresh": 0}

    async def _persist_durable(
        self, chat_id: uuid.UUID, summary: dict | None = None, state: dict | None = None
    ) -> None:
        """Espejo durable en history_chats para sobrevivir reinicio / expiración de Redis."""
        update: dict[str, Any] = {}
        if summary is not None:
            update["summary"] = summary
        if state is not None:
            update["state"] = state
        if not update:
            return
        if not mongo_client.is_connected or mongo_client.db is None:
            return
        await mongo_client.db.history_chats.update_one({"_id": str(chat_id)}, {"$set": update})

    async def _cold_load(self, chat_id: uuid.UUID) -> dict[str, Any] | None:
        """Carga en frío desde Mongo cuando Redis no tiene la conversación, y calienta Redis."""
        if not mongo_client.is_connected or mongo_client.db is None:
            return None

        doc = await mongo_client.db.history_chats.find_one({"_id": str(chat_id)})
        if not doc:
            return None
        summary = doc.get("summary")
        state = doc.get("state")
        if summary is None and state is None:
            return None
        if summary is not None:
            await self._r.set(self._k_summary(chat_id), json.dumps(summary), _MEMORY_TTL)
        if state is not None:
            await self._r.set(self._k_state(chat_id), json.dumps(state), _MEMORY_TTL)
        result_summary = summary or self._empty_summary()
        result_summary.setdefault("turnsSinceRefresh", 0)
        turns = int(await self._r.get(self._k_turns(chat_id)) or 0)
        return {"summary": result_summary, "state": state or {}, "turns": turns}

    # --- API del puerto ---
    async def get(self, chat_id: uuid.UUID) -> dict[str, Any]:
        summary_raw = await self._r.get(self._k_summary(chat_id))
        state_raw = await self._r.get(self._k_state(chat_id))
        if summary_raw is None and state_raw is None:
            cold = await self._cold_load(chat_id)
            if cold is not None:
                return cold

        turns = int(await self._r.get(self._k_turns(chat_id)) or 0)
        base = int(await self._r.get(self._k_base(chat_id)) or 0)
        summary = json.loads(summary_raw) if summary_raw else self._empty_summary()
        summary["turnsSinceRefresh"] = max(turns - base, 0)
        state = json.loads(state_raw) if state_raw else {}
        return {"summary": summary, "state": state, "turns": turns}

    async def bump_turn(self, chat_id: uuid.UUID) -> int:
        return await self._r.incr(self._k_turns(chat_id), _MEMORY_TTL)

    async def save_summary(self, chat_id: uuid.UUID, text: str, version: int) -> None:
        turns = int(await self._r.get(self._k_turns(chat_id)) or 0)
        summary = {"text": text, "version": int(version), "updatedAt": self._now()}
        await self._r.set(self._k_summary(chat_id), json.dumps(summary), _MEMORY_TTL)
        # Base = turno actual -> a partir de aquí turnsSinceRefresh vuelve a 0.
        await self._r.set(self._k_base(chat_id), str(turns), _MEMORY_TTL)
        await self._persist_durable(chat_id, summary=summary)

    async def merge_state(self, chat_id: uuid.UUID, patch: dict[str, Any]) -> None:
        current = await self._r.get(self._k_state(chat_id))
        state = json.loads(current) if current else {}
        state.update(patch or {})
        await self._r.set(self._k_state(chat_id), json.dumps(state), _MEMORY_TTL)
        await self._persist_durable(chat_id, state=state)

    async def mark_processed(self, correlation_id: str) -> bool:
        return await self._r.setnx(self._k_processed(correlation_id), "1", _PROCESSED_TTL)
