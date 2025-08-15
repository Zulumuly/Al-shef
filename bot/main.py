# bot/main.py
import os
import logging
import threading
import asyncio
from dotenv import load_dotenv
from flask import Flask, request, abort

from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

from logic.keyboards.start_button import start
from logic.keyboards.callback import handle_callback, handle_grams_input
from db.database import init_db

# Универсальный импорт / команд
try:
    from logic.commands import cmd_plan, cmd_last, cmd_saved
except ImportError:
    from logic.keyboards.command import cmd_plan, cmd_last, cmd_saved

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# ---------- Flask ----------
flask_app = Flask(__name__)

# ---------- Глобальные объекты PTB ----------
ptb_app: Application | None = None
ptb_loop: asyncio.AbstractEventLoop | None = None

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Exception while handling an update:", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="😅 Что-то пошло не так. Попробуйте ещё раз."
            )
    except Exception:
        pass

def start_ptb_in_background(token: str, webhook_url: str | None, secret: str | None):
    """Создаём event loop в отдельном потоке и запускаем PTB Application."""
    global ptb_app, ptb_loop

    async def _runner():
        # init DB в этом же лупе
        await init_db()

        # Application + хэндлеры
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("plan",  cmd_plan))
        app.add_handler(CommandHandler("last",  cmd_last))
        app.add_handler(CommandHandler("saved", cmd_saved))
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_grams_input))
        app.add_error_handler(on_error)

        # Команды слева от строки ввода
        await app.bot.set_my_commands([
            BotCommand("plan",  "Составить план питания"),
            BotCommand("last",  "План питания"),
            BotCommand("saved", "Сохраненные рецепты"),
        ])

        # Запуск PTB (без встроенного веб-сервера)
        await app.initialize()
        await app.start()

        # Регистрируем вебхук в Telegram на наш Flask-эндпоинт
        if webhook_url:
            await app.bot.set_webhook(url=webhook_url, secret_token=secret, drop_pending_updates=True)
            logging.info("Webhook set: %s", webhook_url)

        # Делаем app/loop доступными снаружи
        global ptb_app
        ptb_app = app

    # Создаём отдельный луп и поток
    ptb_loop = asyncio.new_event_loop()
    def _thread_target():
        asyncio.set_event_loop(ptb_loop)
        ptb_loop.run_until_complete(_runner())
        ptb_loop.run_forever()

    t = threading.Thread(target=_thread_target, daemon=True)
    t.start()

@flask_app.post("/<path:webhook_path>")
def telegram_webhook(webhook_path: str):
    """Принимаем апдейты от Telegram и передаём в PTB Application."""
    secret = (os.getenv("WEBHOOK_SECRET") or "").strip()
    if secret:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header != secret:
            abort(403)

    data = request.get_json(silent=True, force=True)
    if not data:
        return ("bad request", 400)

    if ptb_app is None or ptb_loop is None:
        return ("app not ready", 503)

    update = Update.de_json(data, ptb_app.bot)
    # передаём апдейт асинхронно в PTB
    asyncio.run_coroutine_threadsafe(ptb_app.process_update(update), ptb_loop)
    return ("ok", 200)

def main():
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан")

    base_url = os.getenv("WEBHOOK_BASE_URL")
    if not base_url:
        raise RuntimeError("WEBHOOK_BASE_URL не задан (публичный URL Web Service, напр. https://<name>.onrender.com)")
    url_path = os.getenv("WEBHOOK_PATH", "tg-webhook").lstrip("/")
    secret = (os.getenv("WEBHOOK_SECRET") or "").strip() or None

    # Полный URL, на который Telegram будет слать апдейты
    webhook_url = f"{base_url.rstrip('/')}/{url_path}"

    # Стартуем PTB в фоне
    start_ptb_in_background(token, webhook_url, secret)

    # Поднимаем Flask (биндимся на порт Render)
    port = int(os.getenv("PORT", "10000"))
    logging.info("Flask listening on 0.0.0.0:%s, webhook path: /%s", port, url_path)
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
