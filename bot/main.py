from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN
from db.database import init_db
from logic.keyboards.command import (
    start, handle_products, handle_days, handle_meals, show_saved_plan
)

# Состояния диалога
PRODUCTS, DAYS, MEALS = range(3)


async def main():
    print("🤖 Starting bot (Render-optimized)...")

    # Инициализация базы данных
    await init_db()
    print("✅ Database initialized")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Диалоговое поведение
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
    await app.run_polling(close_loop=False)  # Render-safe


if __name__ == "__main__":
    import asyncio

    try:
        # Проверяем, есть ли уже запущенный event loop (Render)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если Render уже запустил loop — запускаем задачу прямо в нём
            loop.create_task(main())
        else:
            loop.run_until_complete(main())
    except RuntimeError:
        # Резервный сценарий — если Render или Uvicorn блокирует цикл
        asyncio.run(main())
