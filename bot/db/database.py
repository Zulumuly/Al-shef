import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

# ✅ URL базы данных из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ Переменная окружения DATABASE_URL не найдена")

# ✅ Базовый класс для моделей
Base = declarative_base()

# ✅ Асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# ✅ Асинхронная фабрика сессий (именно async_sessionmaker)
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ✅ Создание таблиц при старте
async def init_db():
    """Создание таблиц, если их нет"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized (tables checked/created)")


# ✅ Асинхронный генератор сессий (типобезопасный)
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный контекст для работы с сессией"""
    async with async_session_maker() as session:
        yield session
