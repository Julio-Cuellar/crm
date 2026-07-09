import asyncio
from sqlalchemy import text
from app.platform.db.session import engine


async def backfill():
    async with engine.begin() as conn:
        print("[Backfill] Iniciando copia de clientes a tablas de proyección...")
        
        # 1. conversations_customer_projection
        res1 = await conn.execute(text("""
            INSERT INTO conversations_customer_projection (id, tenant_id, name, phone, email, lead_status, source_updated_at)
            SELECT id, tenant_id, name, phone, email, lead_status, updated_at
            FROM customers
            ON CONFLICT (id) DO NOTHING;
        """))
        print(f"[Backfill] conversations_customer_projection: {res1.rowcount} filas insertadas/procesadas.")
        
        # 2. scheduling_customer_projection
        res2 = await conn.execute(text("""
            INSERT INTO scheduling_customer_projection (id, tenant_id, name, phone, email, source_updated_at)
            SELECT id, tenant_id, name, phone, email, updated_at
            FROM customers
            ON CONFLICT (id) DO NOTHING;
        """))
        print(f"[Backfill] scheduling_customer_projection: {res2.rowcount} filas insertadas/procesadas.")
        
        # 3. tickets_customer_projection
        res3 = await conn.execute(text("""
            INSERT INTO tickets_customer_projection (id, tenant_id, name)
            SELECT id, tenant_id, name
            FROM customers
            ON CONFLICT (id) DO NOTHING;
        """))
        print(f"[Backfill] tickets_customer_projection: {res3.rowcount} filas insertadas/procesadas.")
        
        print("[Backfill] ¡Copia de proyecciones completada con éxito!")


if __name__ == "__main__":
    asyncio.run(backfill())
