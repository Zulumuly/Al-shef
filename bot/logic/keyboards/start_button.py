from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from text import WELCOME_TEXT


# Определяем клавиатуру — как у @iqos_russia_bot
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("🍽️ Составить план питания")],
        [KeyboardButton("📂 Сохранённый план")],
        [KeyboardButton("❤️ Избранные рецепты")]
    ],
    resize_keyboard=True,      # адаптируется под экран
    one_time_keyboard=False,   # остаётся открытой
    input_field_placeholder="Выберите действие ⬇️"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start"""
    await update.message.reply_text(
        f"{WELCOME_TEXT}\n\n"
        "Выберите действие в меню ниже 👇",
        reply_markup=main_keyboard
    )
