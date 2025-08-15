# bot/main.py
import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

from logic.keyboards.start_button import start
from logic.keyboards.callback import handle_callback, handle_grams_input
from db.database import init_db

# Универсальный импорт команд
try:
    from logic.commands import cmd_plan, cmd_last, cmd_saved
except ImportError:
    from logic.keyboards.command import cmd_plan, cmd_last, cmd_saved

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

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

def main() -> None:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN не задан")

    base_url = os.getenv("WEBHOOK_BASE_URL")
    if not base_url:
        raise RuntimeError("WEBHOOK_BASE_URL не задан (публичный HTTPS-URL Web Service)")
    url_path = os.getenv("WEBHOOK_PATH", "tg-webhook").lstrip("/")
    secret = (os.getenv("WEBHOOK_SECRET") or "").strip() or None
    port = int(os.getenv("PORT", "10000"))

    # 1) Инициализируем БД (отдельный краткоживущий цикл)
    asyncio.run(init_db())

    # 2) Создаём приложение
    app = Application.builder().token(bot_token).build()

    # 3) Хэндлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan",  cmd_plan))
    app.add_handler(CommandHandler("last",  cmd_last))
    app.add_handler(CommandHandler("saved", cmd_saved))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_grams_input))
    app.add_error_handler(on_error)

    # 4) Создаём event loop вручную (нужно для Py 3.13 + run_webhook)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 5) Публикуем команды в левом меню (в нашем loop)
    loop.run_until_complete(app.bot.set_my_commands([
        BotCommand("plan",  "Составить план питания"),
        BotCommand("last",  "План питания"),
        BotCommand("saved", "Сохраненные рецепты"),
    ]))
    logging.info("Commands published")

    # 6) Запускаем webhook-сервер (блокирующе)
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=url_path,
        webhook_url=f"{base_url.rstrip('/')}/{url_path}",
        secret_token=secret,
        drop_pending_updates=True,
        # allowed_updates=None,
        # max_connections=40,
    )

if __name__ == "__main__":
    main()
