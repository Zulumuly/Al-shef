import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN
from db.database import init_db
from logic.keyboards.command import start, handle_products, handle_days, handle_meals, show_saved_plan

# Состояния для ConversationHandler
PRODUCTS, DAYS, MEALS = range(3)


async def main():
    print("🤖 Starting bot (async polling)...")

    # Инициализация базы данных
    await init_db()
    print("✅ Database initialized")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обработчик команд
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

    print("🤖 Bot started successfully")
    await app.run_polling(close_loop=False)


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError:
        # Если Render/Jupyter уже запустил event loop
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
