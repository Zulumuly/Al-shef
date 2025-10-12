from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from logic.keyboards.text import WELCOME_TEXT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🍽️ Составить план питания"],
        ["📂 Сохранённый план"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"{WELCOME_TEXT}\n\nВыберите действие:",
        reply_markup=reply_markup
    )
