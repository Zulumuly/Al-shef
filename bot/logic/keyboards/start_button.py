from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from .text import WELCOME_TEXT

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("🍽️ Составить план питания")],
        [KeyboardButton("📂 Сохранённый план")],
        [KeyboardButton("❤️ Избранные рецепты")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Выберите действие ⬇️"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{WELCOME_TEXT}\n\nВыберите действие:",
        reply_markup=main_keyboard
    )
