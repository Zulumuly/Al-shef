import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN
from db.database import init_db
from logic.keyboards.command import (
    start, handle_products, handle_days, handle_meals, show_saved_plan
)

PRODUCTS, DAYS, MEALS = range(3)


async def main():
    print("🤖 Starting bot...")
    await init_db()
    print("✅ Database initialized")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_products)],
            DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_days)],
            MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meals)],
        },
        fallbacks=[CommandHandler("saved", show_saved_plan)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("saved", show_saved_plan))

    print("🤖 Bot started successfully ✅")

    # ⚙️ Главный трюк: используем текущий loop и не закрываем его
    await app.initialize()
    await app.start()
    print("✅ Polling started...")
    await app.updater.start_polling()
    await asyncio.Event().wait()  # держим приложение "вечно"


if __name__ == "__main__":
    # 🔧 Не создаём новый event loop, используем уже существующий
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.create_task(main())
    loop.run_forever()
