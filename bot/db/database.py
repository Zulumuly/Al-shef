# db/database.py
from __future__ import annotations
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool  # <-- ВАЖНО: этот импорт нужен

load_dotenv()

# убираем некорректный PGSSLMODE из окружения (мешает asyncpg)
_bad_pgsslmode = os.environ.get("PGSSLMODE", "")
if _bad_pgsslmode and _bad_pgsslmode.lower() not in {
    "disable", "allow", "prefer", "require", "verify-ca", "verify-full"
}:
    os.environ.pop("PGSSLMODE", None)

RAW_URL = os.getenv("DATABASE_URL", "").strip()

def _normalize_db_url(url: str) -> tuple[str, dict]:
    """Вернёт (нормализованный URL, connect_args) для asyncpg."""
    if not url:
        return "sqlite+aiosqlite:///./bot.db", {}

    # postgres -> postgresql + добавляем asyncpg
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)

    connect_args: dict = {}

    # конвертируем sslmode в ssl для asyncpg
    if "sslmode" in qs:
        mode = (qs.get("sslmode", [""])[0] or "").lower()
        connect_args["ssl"] = False if mode == "disable" else True
        qs.pop("sslmode", None)

    # поддержим ssl=true/false прямо в URL
    if "ssl" in qs:
        val = (qs.get("ssl", [""])[0] or "").lower()
        if val in {"true", "1", "yes"}:
            connect_args["ssl"] = True
        elif val in {"false", "0", "no"}:
            connect_args["ssl"] = False

    # если внешний хост и ssl не задан — включим ssl=True
    host = (parsed.hostname or "").lower()
    is_local = host in {"localhost", "127.0.0.1"} or host.endswith(".internal") or host.endswith(".svc")
    if "ssl" not in connect_args and not is_local:
        connect_args["ssl"] = True

    # убираем ssl/sslmode из query (передаём через connect_args)
    qs.pop("ssl", None)
    qs.pop("sslmode", None)
    url = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))

    return url, connect_args

DATABASE_URL, CONNECT_ARGS = _normalize_db_url(RAW_URL)

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,      # <-- отключаем пул, чтобы не ловить "different loop"
    pool_pre_ping=False,     # <-- без пула пинг не нужен
    connect_args=CONNECT_ARGS,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db() -> None:
    async with engine.begin() as conn:
        from .models import Plan  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
