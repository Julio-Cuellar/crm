import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class InMemoryMongoMock:
    def __init__(self):
        self.history_chats = {}  # key: str(id)
        self.messages = {}       # key: str(id)

    async def list_chats(self, tenant_id: uuid.UUID) -> list:
        tenant_str = str(tenant_id)
        return [
            chat for chat in self.history_chats.values()
            if str(chat.get("tenantId")) == tenant_str
        ]

    async def get_chat_by_customer(self, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> dict | None:
        tenant_str = str(tenant_id)
        customer_str = str(customer_id)
        for chat in self.history_chats.values():
            if str(chat.get("tenantId")) == tenant_str and str(chat.get("customerId")) == customer_str:
                return chat
        return None

    async def save_chat(self, chat: dict) -> dict:
        chat_id = chat.get("_id")
        if not chat_id:
            chat_id = uuid.uuid4()
            chat["_id"] = chat_id
        if "createdAt" not in chat:
            chat["createdAt"] = datetime.now()
        chat["lastMessageAt"] = datetime.now()
        self.history_chats[str(chat_id)] = chat
        return chat

    async def list_messages(self, chat_id: uuid.UUID) -> list:
        chat_str = str(chat_id)
        msgs = [
            msg for msg in self.messages.values()
            if str(msg.get("historyChatId")) == chat_str
        ]
        return sorted(msgs, key=lambda x: x.get("sentAt", datetime.min))

    async def save_message(self, message: dict) -> dict:
        msg_id = message.get("_id")
        if not msg_id:
            msg_id = uuid.uuid4()
            message["_id"] = msg_id
        if "sentAt" not in message:
            message["sentAt"] = datetime.now()
        
        # Guardar mensaje
        self.messages[str(msg_id)] = message
        
        # Actualizar lastMessageAt en la conversación correspondiente
        chat_id = str(message.get("historyChatId"))
        if chat_id in self.history_chats:
            self.history_chats[chat_id]["lastMessageAt"] = message["sentAt"]
            
        return message

    async def update_message_status_by_external_id(self, external_id: str, status: str) -> bool:
        updated = False
        for message in self.messages.values():
            if str(message.get("externalId")) == external_id:
                message["status"] = status
                updated = True
        return updated

class MongoClient:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self.mock = InMemoryMongoMock()

    async def connect(self):
        try:
            print(f"[MongoDB] Conectando a MongoDB en {settings.MONGO_URL}...")
            self.client = AsyncIOMotorClient(settings.MONGO_URL, serverSelectionTimeoutMS=2000)
            # Ping database to verify connection
            await self.client.admin.command('ping')
            self.db = self.client[settings.MONGO_DB]
            self.is_connected = True
            print("[MongoDB] Conexión establecida con éxito.")
            # Crear índices
            await self.db.history_chats.create_index([("customerId", 1), ("tenantId", 1)])
            await self.db.messages.create_index([("historyChatId", 1), ("sentAt", 1)])
            print("[MongoDB] Índices creados correctamente.")
        except Exception as e:
            print(f"[MongoDB Warning] No se pudo conectar a MongoDB: {e}")
            print("[MongoDB Warning] Se utilizará la base de datos en memoria (Mock) para desarrollo.")
            self.is_connected = False
            self.db = None

    async def disconnect(self):
        if self.client:
            self.client.close()
            print("[MongoDB] Conexión cerrada.")

mongo_client = MongoClient()
