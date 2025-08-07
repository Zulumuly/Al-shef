from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from data import TELEGRAM_BOT_TOKEN
from logic.keyboards.start_button import start
from logic.keyboards.callback import handle_callback
from logic.keyboards.product_button import handle_grams_input

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 🟢 Добавляем обработчики
    app.add_handler(CommandHandler("start", start))  
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_grams_input))

    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
