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


async def init_db():
    # Importamos app.infrastructure.db.base para asegurarnos de que todos los modelos 
    # estén registrados en Base.metadata antes de ejecutar el create
    import app.infrastructure.db.base  # noqa: F401

    async with engine.begin() as conn:
        print("[DB] Ejecutando CREATE ALL de tablas (conservando datos existentes)...")
        await conn.run_sync(Base.metadata.create_all)
        print("[DB] Base de datos inicializada correctamente.")


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
