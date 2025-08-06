from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from data import TELEGRAM_BOT_TOKEN
from logic.keyboards.start_button import start
from logic.keyboards.callback import handle_callback

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
