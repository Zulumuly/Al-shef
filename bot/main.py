import asyncio
import logging
import nest_asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config import BOT_TOKEN
from db.database import init_db
from logic.keyboards.command import (
    start,
    new_plan,
    handle_products,
    handle_days,
    handle_meals,
    show_saved_plan,
)

# --- Логирование ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
nest_asyncio.apply()


async def main():
    print("Инициализация базы данных...")
    await init_db()
    print("Database initialized (tables checked/created)")

    print("Запуск Telegram-бота")
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🧠 Создать новый план$"), new_plan)
        ],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_products)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_days)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meals)],
        },
        fallbacks=[],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📋 Показать сохранённый план$"), show_saved_plan))
    app.add_handler(conv_handler)

    print("✅ Бот успешно запущен и готов к работе!")
    await app.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Бот остановлен вручную.")
