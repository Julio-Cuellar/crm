import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


class MongoClient:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False

    async def connect(self):
        print(f"[MongoDB] Conectando a MongoDB en {settings.MONGO_URL}...")
        # Intentar conectar con un timeout corto de 2 segundos para fallar rápido si está apagado
        self.client = AsyncIOMotorClient(settings.MONGO_URL, serverSelectionTimeoutMS=2000)
        # Lanzará una excepción si MongoDB está apagado
        await self.client.admin.command('ping')
        
        self.db = self.client[settings.MONGO_DB]
        self.is_connected = True
        print("[MongoDB] Conexión establecida con éxito.")
        
        # Crear índices
        await self.db.history_chats.create_index([("customerId", 1), ("tenantId", 1)])
        await self.db.messages.create_index([("historyChatId", 1), ("sentAt", 1)])
        print("[MongoDB] Índices creados correctamente.")

    async def disconnect(self):
        if self.client:
            self.client.close()
            print("[MongoDB] Conexión cerrada.")


mongo_client = MongoClient()
