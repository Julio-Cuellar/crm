import asyncio
from app.platform.db.session import engine
from app.platform.db.mongo_client import mongo_client
from sqlalchemy import text


async def debug():
    await mongo_client.connect()
    
    # 1. Read chats from MongoDB
    db_mongo = mongo_client.db
    raw_chats = await db_mongo.history_chats.find({}).to_list(length=100)
    print(f"MongoDB total chats: {len(raw_chats)}")
    
    mongo_customer_ids = []
    for chat in raw_chats:
        cid = chat.get("customerId")
        print(f"Chat ID: {chat['_id']}, TenantId: {chat.get('tenantId')}, CustomerId in Mongo: {cid} (Type: {type(cid)})")
        if cid:
            mongo_customer_ids.append(str(cid))
            
    # 2. Read customers from PostgreSQL customers table
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, tenant_id, name, phone FROM customers;"))
        pg_customers = res.fetchall()
        print(f"\nPG customers table count: {len(pg_customers)}")
        pg_customer_ids = []
        for cust in pg_customers:
            print(f"PG Customer ID: {cust[0]}, TenantId: {cust[1]}, Name: {cust[2]}, Phone: {cust[3]}")
            pg_customer_ids.append(str(cust[0]))
            
        # 3. Read from conversations_customer_projection
        res_proj = await conn.execute(text("SELECT id, tenant_id, name, phone FROM conversations_customer_projection;"))
        proj_customers = res_proj.fetchall()
        print(f"\nPG conversations_customer_projection count: {len(proj_customers)}")
        for cust in proj_customers:
            print(f"Proj Customer ID: {cust[0]}, TenantId: {cust[1]}, Name: {cust[2]}, Phone: {cust[3]}")
            
    # Check if there is intersection
    intersection = set(mongo_customer_ids).intersection(set(pg_customer_ids))
    print(f"\nIntersection of Mongo customerIds and PG customerIds: {intersection}")

    await mongo_client.disconnect()


if __name__ == "__main__":
    asyncio.run(debug())
