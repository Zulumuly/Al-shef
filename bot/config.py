import os

# Проверяем обязательные переменные окружения
required = ["BOT_TOKEN", "DATABASE_URL", "GIGACHAT_AUTH_KEY"]
missing = [var for var in required if not os.getenv(var)]

if missing:
    raise EnvironmentError(f"❌ Не найдены переменные окружения: {', '.join(missing)}")

# Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL")

# GigaChat credentials
GIGACHAT_AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")  # по умолчанию для физлиц
