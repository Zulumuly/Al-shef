import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN
from db.database import init_db
from logic.keyboards.command import (
    start, handle_products, handle_days, handle_meals, show_saved_plan
)

# Состояния
PRODUCTS, DAYS, MEALS = range(3)


async def start_bot():
    print("🤖 Starting bot (Render-stable)...")

    # ✅ Инициализация базы данных в том же event loop
    await init_db()
    print("✅ Database initialized")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_products)],
            DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_days)],
            MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meals)],
        },
        fallbacks=[CommandHandler("saved", show_saved_plan)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("saved", show_saved_plan))

    print("🤖 Bot started successfully ✅")
    await app.run_polling(close_loop=False)


# === Точка входа ===
if __name__ == "__main__":
    try:
        # Проверяем, запущен ли event loop
        loop = asyncio.get_event_loop()

        # Если Render уже запустил loop — просто создаём задачу внутри него
        if loop.is_running():
            print("⚙️ Event loop already running — scheduling bot inside existing loop.")
            asyncio.ensure_future(start_bot())
        else:
            # Локальный запуск
            loop.run_until_complete(start_bot())

    except RuntimeError:
        # Резервный случай (если Render или другой рантайм странно себя ведёт)
        print("⚙️ Fallback: creating a new asyncio loop manually.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_bot())
