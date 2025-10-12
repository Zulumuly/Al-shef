from telegram.ext import (
    ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
)
from config import BOT_TOKEN
from db.database import Base, engine
from logic.keyboards.start_button import start
from logic.keyboards.command import (
    plan_start, process_products, process_days, process_meals,
    handle_text_buttons, show_saved,
    WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS
)

async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saved", show_saved))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("plan", plan_start),
            MessageHandler(filters.Regex(".*Составить план питания.*"), plan_start)
        ],
        states={
            WAITING_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_products)],
            WAITING_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_days)],
            WAITING_MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_meals)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_buttons))

    app.post_init = on_startup
    print("🤖 Bot started successfully")
    app.run_polling()

if __name__ == "__main__":
    main()
