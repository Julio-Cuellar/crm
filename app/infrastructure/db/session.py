from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from sqlalchemy import text
from app.infrastructure.db.base_class import Base

# Importamos las entidades del sistema (deben importarse antes de crear/borrar las tablas)
# Crearemos un archivo central base.py que contenga todas estas importaciones.

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_db(force_drop: bool = False):
    import app.infrastructure.db.base  # noqa: F401

    async with engine.begin() as conn:
        if force_drop:
            print("[DB] Ejecutando DROP ALL (force_drop=True)...")
            await conn.run_sync(Base.metadata.drop_all)
        print("[DB] Creando tablas si no existen...")
        await conn.run_sync(Base.metadata.create_all)
        print("[DB] Inicialización de base de datos completada.")


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
