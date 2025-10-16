import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Переменная окружения DATABASE_URL не найдена")


Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db():
    """Создание таблиц, если их нет"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized (tables checked/created)")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный контекст для работы с сессией"""
    async with async_session_maker() as session:
        yield session
