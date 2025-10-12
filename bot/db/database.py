from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

Base = declarative_base()

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Создаем фабрику сессий
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Асинхронная инициализация базы данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Получение сессии
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
