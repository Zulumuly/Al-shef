from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from logic.llm.meal_plan_generator import generate_meal_plan
from db.crud import create_meal_plan, get_meal_plan


async def handle_products(update, context):
    context.user_data["products"] = update.message.text.strip()
    await update.message.reply_text("На сколько дней составить план питания?")
    return 1  # DAYS


async def handle_days(update, context):
    context.user_data["days"] = update.message.text.strip()
    await update.message.reply_text("Сколько приёмов пищи в день?")
    return 2  # MEALS


async def handle_meals(update, context):
    products = context.user_data.get("products")
    days = context.user_data.get("days")
    meals_per_day = update.message.text.strip()

    await update.message.reply_text("⏳ Формирую план питания, подождите немного...")

    plan_text = generate_meal_plan(products, days, meals_per_day)

    user_id = str(update.message.from_user.id)
    await create_meal_plan(user_id, products, days, meals_per_day, plan_text)

    await update.message.reply_text("✅ План питания сохранён в базе данных.\n\n" + plan_text)
    return ConversationHandler.END


async def show_saved_plan(update, context):
    user_id = str(update.message.from_user.id)
    plan = await get_meal_plan(user_id)

    if plan:
        await update.message.reply_text(f"📋 Ваш сохранённый план:\n\n{plan.plan_text}")
    else:
        await update.message.reply_text("Пока нет сохранённых планов 😔")
