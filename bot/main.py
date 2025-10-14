import asyncio
import logging
import nest_asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
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
    handle_save_plan,
    handle_new_plan,
    show_saved_plan,
    ASK_PRODUCTS,
    ASK_DAYS,
    ASK_MEALS,
)

# --- Логирование ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
nest_asyncio.apply()


async def main():
    print("🚀 Инициализация базы данных...")
    await init_db()
    print("✅ Database initialized (tables checked/created)")

    print("🤖 Запуск Telegram-бота...")
    app = Application.builder().token(BOT_TOKEN).build()

    # --- Обработчик создания плана ---
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🧠 Plan$"), new_plan)],
        states={
            ASK_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_products)],
            ASK_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_days)],
            ASK_MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meals)],
        },
        fallbacks=[],
        per_message=False,
    )

    # --- Регистрация всех обработчиков ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^📋 Saved$"), show_saved_plan))
    app.add_handler(CallbackQueryHandler(handle_save_plan, pattern="save_plan"))
    app.add_handler(CallbackQueryHandler(handle_new_plan, pattern="new_plan"))

    print("✅ Бот успешно запущен и готов к работе!")
    await app.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Бот остановлен вручную.")
