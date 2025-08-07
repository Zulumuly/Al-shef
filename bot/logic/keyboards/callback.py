# callback.py

from telegram import Update
from telegram.ext import ContextTypes
from .product_button import category_menu, product_keyboards, get_product_name

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "input_products":
        context.user_data["ingredients"] = []
        context.user_data["step"] = None
        await query.message.reply_text("Выбери категорию продуктов:", reply_markup=category_menu)

    elif data.startswith("cat_"):
        keyboard = product_keyboards.get(data)
        if keyboard:
            await query.message.reply_text("Выбери продукт:", reply_markup=keyboard)

    elif data.startswith("prod_"):
        product = get_product_name(data)
        if product:
            context.user_data["selected_product"] = product
            context.user_data["step"] = "waiting_for_grams"
            await query.message.reply_text(f"Введите количество в граммах для продукта: {product}")

    elif data == "view_plan":
        await query.message.reply_text("Пока планов нет.")

    elif data == "saved_recipes":
        await query.message.reply_text("Сохраненных рецептов пока нет.")

    elif data == "back_to_categories":
        await query.message.reply_text("Выбери категорию продуктов:", reply_markup=category_menu)

    elif data == "add_more_products":
        context.user_data["selected_product"] = None
        context.user_data["step"] = None
        await query.message.reply_text("Выбери следующую категорию:", reply_markup=category_menu)

    elif data == "choose_meals_days":
        context.user_data["step"] = "waiting_for_days"
        await query.message.reply_text("Сколько дней планируем питание? (Напиши число)")


    


