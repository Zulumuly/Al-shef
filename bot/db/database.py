from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

# Базовая модель
Base = declarative_base()

# Асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Фабрика сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Асинхронная инициализация базы данных
async def init_db() -> None:
    """Создаёт все таблицы в базе данных (если их нет)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Асинхронный генератор для получения сессии
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Возвращает асинхронную сессию SQLAlchemy."""
    async with AsyncSessionLocal() as session:
        yield session
