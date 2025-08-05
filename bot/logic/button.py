from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["✅ Внести список продуктов"],
        ["📅 Посмотреть план питания"],
        ["⭐ Сохранённые рецепты"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Привет! Я помогу тебе с питанием. Выбери действие:",
        reply_markup=reply_markup
    )

# Обработка нажатий на кнопки
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "✅ Внести список продуктов":
        await update.message.reply_text("✍️ Введите список продуктов вручную.")
    elif text == "📅 Посмотреть план питания":
        await update.message.reply_text("🗓 План питания пока пуст.")
    elif text == "⭐ Сохранённые рецепты":
        await update.message.reply_text("⭐ Здесь будут отображаться сохранённые рецепты.")
    else:
        await update.message.reply_text("❓ Неизвестная команда. Пожалуйста, выбери один из пунктов меню.")


        