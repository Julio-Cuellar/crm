import asyncio
import uuid
from app.platform.db.session import async_session_factory
from app.platform.db.mongo_client import mongo_client
from app.modules.conversations.infrastructure.db.repositories.mongo_chat_history_repository import MongoChatHistoryRepository
from app.modules.conversations.infrastructure.db.repositories.customer_projection_repository import CustomerProjectionRepository


async def test_list_chats():
    tenant_id = uuid.UUID("5ed79324-5b0d-44b5-9ff8-a567eadb8785")
    await mongo_client.connect()
    
    mongo_repo = MongoChatHistoryRepository()
    raw_chats = await mongo_repo.list_chats_by_tenant(tenant_id)
    print(f"Chats in Mongo for tenant {tenant_id}: {len(raw_chats)}")
    
    # 1. Unique customer IDs
    customer_ids = []
    for rc in raw_chats:
        cid = rc.get("customerId")
        if cid:
            try:
                customer_ids.append(uuid.UUID(str(cid)))
            except ValueError:
                continue
    print(f"Customer IDs in chats: {customer_ids}")
    
    # 2. Query Postgres using AsyncSession
    async with async_session_factory() as session:
        projection_repo = CustomerProjectionRepository(session)
        projections = await projection_repo.get_by_ids(customer_ids)
        print(f"Projections found in DB: {len(projections)}")
        for proj in projections:
            print(f"Found Projection: ID={proj.id}, Name={proj.name}, Phone={proj.phone}")
            
        customers_map = {c.id: c for c in projections}
        
        # Mimic chats list construction
        for raw_chat in raw_chats:
            customer_id_str = raw_chat.get("customerId")
            if not customer_id_str:
                continue
            customer_id = uuid.UUID(str(customer_id_str))
            customer = customers_map.get(customer_id)
            if not customer:
                print(f"Chat {raw_chat['_id']}: Customer {customer_id} NOT FOUND in map! (Defaulting to Cliente Desconocido)")
            else:
                print(f"Chat {raw_chat['_id']}: Customer {customer_id} FOUND! Name={customer.name}")

    await mongo_client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_list_chats())
