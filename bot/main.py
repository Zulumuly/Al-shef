import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ConversationHandler,  
    ContextTypes,
    filters,
)
from db.database import init_db
from logic.keyboards.command import handle_products, handle_days, handle_meals, show_saved_plan


# Состояния диалога
PRODUCTS, DAYS, MEALS = range(3)


# Нижнее меню
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [["Составить план питания", "Сохранённый план"]],
        resize_keyboard=True
    )


# Стартовое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет 👋 Я помогу тебе составить план питания.\nВыбери действие:",
        reply_markup=main_menu_keyboard()
    )


# Обработка нажатия кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Составить план питания":
        await update.message.reply_text("Введите список продуктов (через запятую):")
        return PRODUCTS

    elif text == "Сохранённый план":
        await show_saved_plan(update, context)
        return ConversationHandler.END

    else:
        await update.message.reply_text("Пожалуйста, выберите действие с помощью кнопок ниже 👇")
        return ConversationHandler.END


# Основной диалог
conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
    states={
        PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_products)],
        DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_days)],
        MEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meals)],
    },
    fallbacks=[],
)


async def main():
    print("🤖 Starting bot...")
    await init_db()
    print("✅ Database initialized")

    from config import BOT_TOKEN
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Добавляем только ConversationHandler
    app.add_handler(conv_handler)

    await app.initialize()
    await app.start()
    print("🤖 Bot started successfully ✅")

    await app.updater.start_polling()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
