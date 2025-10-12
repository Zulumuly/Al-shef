import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator

# URL базы из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Базовый класс для моделей
Base = declarative_base()

# Асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Асинхронная фабрика сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ✅ Создание таблиц при старте
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized (tables checked/created)")


# ✅ Асинхронный генератор сессий (типобезопасный, без ошибок Pylance)
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
