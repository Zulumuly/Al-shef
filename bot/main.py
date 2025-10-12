import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from config import BOT_TOKEN
from db.database import init_db

from logic.keyboards.command import (
    start,
    handle_start_plan,
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- Основной диалоговый обработчик ---
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_start_plan, pattern="create_plan")],
    states={
        ASK_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_products)],
        ASK_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_days)],
        ASK_MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meals)],
    },
    fallbacks=[],
)


# --- Основная функция запуска ---
async def main():
    print("🚀 Инициализация базы данных...")
    await init_db()

    print("🤖 Запуск Telegram-бота...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 🔹 Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(show_saved_plan, pattern="show_saved"))
    app.add_handler(CallbackQueryHandler(handle_save_plan, pattern="save_plan"))
    app.add_handler(CallbackQueryHandler(handle_new_plan, pattern="new_plan"))

    print("✅ Бот успешно запущен и готов к работе!")

    await app.run_polling()


if __name__ == "__main__":
    try:
        import nest_asyncio
        import asyncio

        nest_asyncio.apply()  # ✅ Позволяет использовать уже запущенный event loop
        asyncio.get_event_loop().run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Бот остановлен вручную.")