import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GIGACHAT_TOKEN = os.environ.get("GIGACHAT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")  # например: postgresql+asyncpg://user:pass@host/db

# Проверка, чтобы не запускать без конфигурации
missing = [k for k, v in {
    "BOT_TOKEN": BOT_TOKEN,
    "GIGACHAT_TOKEN": GIGACHAT_TOKEN,
    "DATABASE_URL": DATABASE_URL
}.items() if not v]

if missing:
    raise EnvironmentError(f"❌ Не найдены переменные окружения: {', '.join(missing)}")
