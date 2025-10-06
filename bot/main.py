# bot/main.py
# bot/main.py
import os
import logging
import asyncio
from dotenv import load_dotenv

from telegram import BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

from logic.keyboards.start_button import start
from logic.keyboards.callback import handle_callback, handle_text_input
from db.database import init_db

# Универсальный импорт команд
try:
    from logic.commands import cmd_plan, cmd_last, cmd_saved, cmd_help
except ImportError:
    # Фоллбек-функции
    async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Введите список продуктов и их количество (в граммах):\n\n"
            "Например:\n"
            "курица 500 г\n"
            "рис 200 г\n" 
            "помидоры 300 г\n\n"
            "После этого я подберу рецепты и составлю план питания 🍽"
        )
        context.user_data["awaiting_ingredients"] = True
    
    async def cmd_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Пока сохранённых планов нет.")
    
    async def cmd_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Сохранённых планов пока нет.")
    
    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Помощь по боту:\n"
            "/plan - составить план питания\n"
            "/last - последний план\n"
            "/saved - сохраненные планы"
        )

# Настройка логирования
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

async def main():
    """Основная функция для Background Worker"""
    load_dotenv()
    
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан в переменных окружения")
    
    logger.info("Starting bot in polling mode...")
    
    # Инициализация БД
    await init_db()
    logger.info("Database initialized successfully")

    # Создаем Application
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("plan", cmd_plan))
    application.add_handler(CommandHandler("last", cmd_last))
    application.add_handler(CommandHandler("saved", cmd_saved))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    application.add_error_handler(on_error)

    # Настраиваем меню команд
    await application.bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("plan", "Составить план питания"),
        BotCommand("last", "Последний план питания"), 
        BotCommand("saved", "Сохраненные планы"),
        BotCommand("help", "Помощь"),
    ])
    logger.info("Bot commands set successfully")

    # Запускаем бота в режиме polling (для Background Worker)
    logger.info("🤖 Bot started in polling mode")
    await application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        close_loop=False  # Важно для Render
    )

if __name__ == "__main__":
    # Запускаем асинхронно
    asyncio.run(main())