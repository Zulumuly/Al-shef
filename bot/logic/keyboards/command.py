from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from db.crud import create_meal_plan, get_meal_plan
from logic.llm.meal_plan_generator import generate_meal_plan

WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS = range(3)

async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите список доступных продуктов через запятую:")
    return WAITING_PRODUCTS

async def process_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["products"] = [p.strip() for p in update.message.text.split(",") if p.strip()]
    await update.message.reply_text("На сколько дней вы хотите составить план?")
    return WAITING_DAYS

async def process_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число дней (например, 3):")
        return WAITING_DAYS
    context.user_data["days"] = days
    await update.message.reply_text("Сколько приёмов пищи в день?")
    return WAITING_MEALS

async def process_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        meals = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число (например, 4):")
        return WAITING_MEALS

    products = context.user_data["products"]
    days = context.user_data["days"]

    await update.message.reply_text("⏳ Генерирую план питания...")

    plan_text = generate_meal_plan(products, days, meals)

    await create_meal_plan(
        user_id=str(update.effective_user.id),
        products=products,
        days=days,
        meals=meals,
        plan_text=plan_text
    )

    await update.message.reply_text(f"✅ Ваш план питания:\n\n{plan_text}")
    return ConversationHandler.END

async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = await get_meal_plan(str(update.effective_user.id))
    if not plan:
        await update.message.reply_text("❌ У вас нет сохранённого плана.")
    else:
        await update.message.reply_text(f"📋 Ваш сохранённый план:\n\n{plan.plan_text}")

async def handle_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "составить план" in text:
        return await plan_start(update, context)
    elif "сохранённый план" in text:
        return await show_saved(update, context)
    elif "избранные" in text:
        await update.message.reply_text("❤️ Раздел 'Избранные рецепты' пока в разработке.")
    else:
        await update.message.reply_text("Я не понимаю эту команду 😅. Попробуйте выбрать из меню.")
