from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from .product_button import category_menu  # создадим позже

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "input_products":
        context.user_data["ingredients"] = []
        await query.message.reply_text("Выбери категорию продуктов:", reply_markup=category_menu)

    elif data == "view_plan":
        await query.message.reply_text("Пока планов нет.")

    elif data == "saved_recipes":
        await query.message.reply_text("Сохраненных рецептов пока нет.")
