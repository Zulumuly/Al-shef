import os
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()

# --- Подключение только к Render Postgres ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL не найден. Установи переменную окружения в Render.")

# Render иногда выдаёт "postgres://", но SQLAlchemy требует "postgresql+psycopg://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

logger.info(f"Using DATABASE_URL: {DATABASE_URL}")

# Создаём движок
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("LOG_LEVEL") == "DEBUG",  # логируем SQL, если DEBUG
    future=True
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# --- Хелперы -------------------------------------------------------------------

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Возвращает асинхронную сессию для работы с БД."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Создаёт таблицы, если их ещё нет."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ База данных инициализирована")


async def close_db():
    """Закрывает соединение с базой данных."""
    await engine.dispose()
    logger.info("🔒 Соединение с базой закрыто")
