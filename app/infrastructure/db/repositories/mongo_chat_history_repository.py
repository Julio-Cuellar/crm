import uuid
from datetime import datetime
from app.domain.ports.chat_history_repository import ChatHistoryRepository
from app.infrastructure.db.mongo.mongo_client import mongo_client

class MongoChatHistoryRepository(ChatHistoryRepository):
    async def get_or_create_chat(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID, platform: str = "WHATSAPP", external_thread_id: str | None = None
    ) -> dict:
        if not mongo_client.is_connected:
            chat = await mongo_client.mock.get_chat_by_customer(tenant_id, customer_id)
            if chat:
                return chat
            new_chat = {
                "_id": uuid.uuid4(),
                "tenantId": tenant_id,
                "customerId": customer_id,
                "platform": platform,
                "externalThreadId": external_thread_id or "",
                "status": "ACTIVE",
                "createdAt": datetime.now(),
                "lastMessageAt": datetime.now()
            }
            return await mongo_client.mock.save_chat(new_chat)
            
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
        if not mongo_client.is_connected:
            return await mongo_client.mock.list_chats(tenant_id)
            
        db = mongo_client.db
        cursor = db.history_chats.find({"tenantId": str(tenant_id)})
        chats = await cursor.to_list(length=100)
        return chats

    async def get_messages_by_chat_id(self, chat_id: uuid.UUID) -> list[dict]:
        if not mongo_client.is_connected:
            return await mongo_client.mock.list_messages(chat_id)
            
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
        if not mongo_client.is_connected:
            new_msg = {
                "_id": uuid.uuid4(),
                "historyChatId": chat_id,
                "direction": direction,
                "type": message_type,
                "content": content,
                "externalId": external_id or "",
                "mediaUrl": media_url,
                "sentAt": now,
                "status": status
            }
            return await mongo_client.mock.save_message(new_msg)
            
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
        if not mongo_client.is_connected:
            return await mongo_client.mock.update_message_status_by_external_id(external_id, status)

        db = mongo_client.db
        result = await db.messages.update_one(
            {"externalId": external_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
