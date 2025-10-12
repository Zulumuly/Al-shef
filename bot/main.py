import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)
from config import BOT_TOKEN
from db.database import init_db
from logic.keyboards.command import (
    plan_start,
    process_products,
    process_days,
    process_meals,
    handle_plan_choice,
    show_saved,
    WAITING_PRODUCTS,
    WAITING_DAYS,
    WAITING_MEALS,
    CONFIRM_PLAN,
)
from logic.keyboards.start_button import start


async def main():
    print("🤖 Starting bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # === Диалог для составления плана ===
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("plan", plan_start)],
        states={
            WAITING_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_products)],
            WAITING_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_days)],
            WAITING_MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_meals)],
            CONFIRM_PLAN: [CallbackQueryHandler(handle_plan_choice)],
        },
        fallbacks=[],
    )

    # === Команды ===
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saved", show_saved))
    app.add_handler(conv_handler)

    # === Инициализация базы ===
    await init_db()
    print("✅ Database initialized")

    # === Запуск ===
    print("🤖 Bot started successfully")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
