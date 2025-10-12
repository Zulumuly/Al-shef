from telegram.ext import (
    ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
)
from config import BOT_TOKEN
from db.database import Base, engine
from logic.keyboards.start_button import start
from logic.keyboards.command import (
    plan_start, process_products, process_days, process_meals,
    show_saved,
    WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS
)

# --- Инициализация БД при запуске ---
async def on_startup(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")

# --- Главная функция ---
def main():
    # создаём приложение Telegram
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saved", show_saved))

    # диалог: план питания
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("plan", plan_start),
            MessageHandler(filters.Regex(".*Составить план питания.*"), plan_start),
        ],
        states={
            WAITING_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_products)],
            WAITING_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_days)],
            WAITING_MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_meals)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)

    # обработчик для кнопки "📂 Сохранённый план"
    app.add_handler(MessageHandler(filters.Regex(".*Сохранённый план.*"), show_saved))

    print("🤖 Bot started successfully")
    app.post_init = on_startup
    app.run_polling()

# --- Запуск ---
if __name__ == "__main__":
    main()
