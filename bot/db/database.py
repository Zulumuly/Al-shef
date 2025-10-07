# db/database.py
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()

engine = None
async_session = None


def get_database_url() -> str:
    """Получает URL базы данных из переменных окружения (Render или локально)."""
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Приводим к асинхронному формату
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        logger.info("Using DATABASE_URL from environment")
        return database_url

    # Фоллбэк для локальной разработки
    logger.warning("DATABASE_URL not found — using local SQLite database.")
    return "sqlite+aiosqlite:///./alshef.db"


async def init_db():
    """Инициализация базы данных."""
    global engine, async_session

    try:
        database_url = get_database_url()
        logger.info(f"Initializing database: {database_url}")

        engine = create_async_engine(
            database_url,
            echo=os.getenv("LOG_LEVEL") == "DEBUG",
            future=True
        )

        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.exception(f"Failed to initialize database: {e}")
        raise


async def get_session() -> AsyncSession:
    """Возвращает асинхронную сессию."""
    if async_session is None:
        await init_db()

    async with async_session() as session:
        yield session


async def close_db():
    """Закрывает соединение с базой данных."""
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")
