import uuid
from datetime import datetime
from app.modules.conversations.domain.ports.chat_history_repository import ChatHistoryRepository
from app.modules.conversations.infrastructure.db.mongo.mongo_client import mongo_client


class MongoChatHistoryRepository(ChatHistoryRepository):
    async def get_or_create_chat(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID, platform: str = "WHATSAPP", external_thread_id: str | None = None
    ) -> dict:
        db = mongo_client.db
        chat = await db.history_chats.find_one({
            "customerId": str(customer_id),
            "tenantId": str(tenant_id)
        })
        if chat:
            return chat

        new_chat = {
            "_id": str(uuid.uuid4()),
            "tenantId": str(tenant_id),
            "customerId": str(customer_id),
            "platform": platform,
            "externalThreadId": external_thread_id or "",
            "status": "ACTIVE",
            "createdAt": datetime.now(),
            "lastMessageAt": datetime.now()
        }
        await db.history_chats.insert_one(new_chat)
        return new_chat

    async def list_chats_by_tenant(self, tenant_id: uuid.UUID) -> list[dict]:
        db = mongo_client.db
        cursor = db.history_chats.find({"tenantId": str(tenant_id)})
        chats = await cursor.to_list(length=100)
        return chats

    async def get_messages_by_chat_id(self, chat_id: uuid.UUID) -> list[dict]:
        db = mongo_client.db
        cursor = db.messages.find({"historyChatId": str(chat_id)}).sort("sentAt", 1)
        messages = await cursor.to_list(length=500)
        return messages

    async def save_message(
        self,
        chat_id: uuid.UUID,
        direction: str,
        message_type: str,
        content: str,
        external_id: str | None = None,
        media_url: str | None = None,
        status: str = "SENT"
    ) -> dict:
        now = datetime.now()
        db = mongo_client.db
        new_msg = {
            "_id": str(uuid.uuid4()),
            "historyChatId": str(chat_id),
            "direction": direction,
            "type": message_type,
            "content": content,
            "externalId": external_id or "",
            "mediaUrl": media_url,
            "sentAt": now,
            "status": status
        }
        await db.messages.insert_one(new_msg)
        await db.history_chats.update_one(
            {"_id": str(chat_id)},
            {"$set": {"lastMessageAt": now}}
        )
        return new_msg

    async def update_message_status_by_external_id(self, external_id: str, status: str) -> bool:
        db = mongo_client.db
        result = await db.messages.update_one(
            {"externalId": external_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
