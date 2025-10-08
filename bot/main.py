# bot/main.py
import os
import logging
import asyncio
from dotenv import load_dotenv

from telegram import BotCommand, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

from logic.keyboards.callback import handle_callback, handle_text_input
from db.database import init_db

# Импорт команд
try:
    from logic.keyboards.command import cmd_last, cmd_saved
except ImportError:
    async def cmd_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Пока сохранённых планов нет.")

    async def cmd_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Сохранённых планов пока нет.")

# --- Логирование ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)


# --- Стартовая команда (создание плана) ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите список продуктов и их количество (в граммах):\n\n"
        "Например:\n"
        "курица 500 г\n"
        "рис 200 г\n"
        "помидоры 300 г\n\n"
        "После этого я подберу рецепты и составлю план питания 🍽"
    )
    context.user_data["awaiting_ingredients"] = True


async def main():
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан в переменных окружения")

    logger.info("Starting bot in polling mode...")

    await init_db()
    logger.info("Database initialized successfully")

    application = Application.builder().token(token).build()

    # Регистрируем только нужные команды
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("last", cmd_last))
    application.add_handler(CommandHandler("saved", cmd_saved))

    # Callback и текст
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Ошибки
    application.add_error_handler(on_error)

    # Меню команд
    await application.bot.set_my_commands([
        BotCommand("start", "Составить план питания"),
        BotCommand("last", "Последний план питания"),
        BotCommand("saved", "Сохранённые планы"),
    ])

    logger.info("🤖 Bot started in polling mode")
    await application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        close_loop=False
    )


if __name__ == "__main__":
    asyncio.run(main())
