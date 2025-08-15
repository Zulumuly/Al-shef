# bot/main.py
import os
import logging
import asyncio
import signal
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

from logic.keyboards.start_button import start
from logic.keyboards.callback import handle_callback, handle_grams_input
from db.database import init_db

# Универсальный импорт команд (поддержит оба размещения файла)
try:
    from logic.commands import cmd_plan, cmd_last, cmd_saved
except ImportError:
    from logic.keyboards.command import cmd_plan, cmd_last, cmd_saved  # если файл у тебя тут

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

async def bootstrap() -> None:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN не задан в .env")

    # Инициализация БД в том же event loop, что и приложение
    await init_db()

    app = Application.builder().token(bot_token).build()

    # Хэндлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan",  cmd_plan))
    app.add_handler(CommandHandler("last",  cmd_last))
    app.add_handler(CommandHandler("saved", cmd_saved))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_grams_input))
    app.add_error_handler(on_error)

    # Ожидание по сигналам
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass  # Windows / некоторые среды

    async with app:
        # Публикуем команды для меню слева от строки ввода
        await app.bot.set_my_commands([
            BotCommand("plan",  "Составить план питания"),
            BotCommand("last",  "План питания"),
            BotCommand("saved", "Сохраненные рецепты"),
        ])

        # В PTB 21.x этого достаточно, чтобы начать polling
        await app.start()
        print("✅ Бот запущен (polling)")

        try:
            await stop_event.wait()  # ждём Ctrl+C / SIGTERM
        finally:
            await app.stop()
            await app.shutdown()

if __name__ == "__main__":
    asyncio.run(bootstrap())
