# bot/config.py
import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = ["BOT_TOKEN", "DATABASE_URL", "GIGACHAT_CLIENT_ID", "GIGACHAT_CLIENT_SECRET"]

missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing:
    raise EnvironmentError(f"Не найдены переменные окружения: {', '.join(missing)}")

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")
GIGACHAT_SCOPE = "GIGACHAT_API_PERS"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "logic", "llm", "sber.pem")
