# bot/config.py
import os
from dotenv import load_dotenv

# Загружаем .env если он есть (локально)
load_dotenv()

# Обязательные переменные
REQUIRED_VARS = ["BOT_TOKEN", "DATABASE_URL", "GIGACHAT_CLIENT_ID", "GIGACHAT_CLIENT_SECRET"]

missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing:
    raise EnvironmentError(f"❌ Не найдены переменные окружения: {', '.join(missing)}")

# Телеграм токен
BOT_TOKEN = os.getenv("BOT_TOKEN")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL")

# GigaChat
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")

# Скоуп для физлиц
GIGACHAT_SCOPE = "GIGACHAT_API_PERS"

# Путь к сертификату
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "logic", "llm", "sber.pem")
