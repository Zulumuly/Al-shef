import asyncio
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
from db.database import Base, engine
from logic.keyboards.start_button import start
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

# ——————————————————————————————————————————————
async def on_startup(_: ApplicationBuilder):
    """Создание таблиц БД при запуске"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")


# ——————————————————————————————————————————————
def main():
    print("🚀 Starting bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    # ——— Команда /start
    app.add_handler(CommandHandler("start", start))

    # ——— Команда /saved
    app.add_handler(CommandHandler("saved", show_saved))

    # ——— Основной ConversationHandler для создания плана
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("plan", plan_start),
            MessageHandler(filters.Regex(".*Составить план питания.*"), plan_start),
        ],
        states={
            WAITING_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_products)],
            WAITING_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_days)],
            WAITING_MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_meals)],
            CONFIRM_PLAN: [CallbackQueryHandler(handle_plan_choice)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)

    # ——— Запуск
    print("🤖 Bot started successfully")
    app.run_polling(drop_pending_updates=True)


# ——————————————————————————————————————————————
if __name__ == "__main__":
    main()
