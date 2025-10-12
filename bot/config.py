import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GIGACHAT_TOKEN = os.environ.get("GIGACHAT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

missing = [name for name, val in {
    "BOT_TOKEN": BOT_TOKEN,
    "GIGACHAT_TOKEN": GIGACHAT_TOKEN,
    "DATABASE_URL": DATABASE_URL,
}.items() if not val]

if missing:
    raise EnvironmentError(f"❌ Не найдены переменные окружения: {', '.join(missing)}")
