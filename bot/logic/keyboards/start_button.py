from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from logic.text import WELCOME_TEXT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🥗 Составить план питания", callback_data="input_products")],
        [InlineKeyboardButton("📅 Посмотреть сохраненный план", callback_data="view_plan")],
        [InlineKeyboardButton("📘 Сохраненные рецепты", callback_data="saved_recipes")]
    ])
    await update.message.reply_text(WELCOME_TEXT, reply_markup=keyboard)
