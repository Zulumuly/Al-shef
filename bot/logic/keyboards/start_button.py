# bot/logic/keyboards/start_button.py
from telegram import Update
from telegram.ext import ContextTypes
from bot.logic.text import WELCOME_TEXT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{WELCOME_TEXT}\n\n"
        "Действия доступны в меню:\n"
        "🍽️ /start — составить план питания\n"
        "📂 /saved — сохранённый план питания\n"
        "❤️ /like — сохранённые рецепты"
    )
