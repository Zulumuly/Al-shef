from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters
)
from bot.config import BOT_TOKEN
from bot.logic.keyboards.start_button import start
from bot.logic.keyboards.commands import (
    plan_start, process_products, process_days, process_meals,
    handle_text_buttons, show_saved,
    WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS
)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- /start ---
    app.add_handler(CommandHandler("start", start))

    # --- /saved ---
    app.add_handler(CommandHandler("saved", show_saved))

    # --- Диалог составления плана ---
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

    # --- Обработка нажатий кнопок меню ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_buttons))

    print("🤖 Bot started successfully")
    app.run_polling()

if __name__ == "__main__":
    main()
