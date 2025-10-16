from telegram import Update
from telegram.ext import ContextTypes
from .text import WELCOME_TEXT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие"""
    await update.message.reply_text(
        f"{WELCOME_TEXT}\n\n"
        "Доступные команды:\n"
        "/plan — составить план питания\n"
        "/saved — сохранённый план питания"
    )
