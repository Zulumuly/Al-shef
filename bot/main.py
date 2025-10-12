import asyncio
import warnings
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
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
from config import BOT_TOKEN
from db.database import Base, engine


# 🔇 скрываем предупреждения PTBUserWarning
warnings.filterwarnings("ignore", category=UserWarning, module="telegram")


async def on_startup():
    """Создать таблицы базы при старте"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")


async def main():
    print("🤖 Starting bot (async polling)...")

    # создаём приложение
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan_start))
    app.add_handler(CommandHandler("saved", show_saved))

    # диалог составления плана
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("plan", plan_start)],
        states={
            WAITING_PRODUCTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_products)
            ],
            WAITING_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_days)
            ],
            WAITING_MEALS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_meals)
            ],
            CONFIRM_PLAN: [
                CallbackQueryHandler(handle_plan_choice)
            ],
        },
        fallbacks=[],
        per_message=False,
    )

    app.add_handler(conv_handler)

    await on_startup()
    print("🤖 Bot started successfully")

    # ❗ корректный запуск polling в PTB v21+
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
