from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from db.crud import create_meal_plan, get_meal_plan
from logic.llm.meal_plan_generator import generate_meal_plan

WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS = range(3)

# Шаг 1: начало — запросить продукты
async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите список доступных продуктов через запятую:")
    return WAITING_PRODUCTS

# Шаг 2: получить продукты
async def process_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Пожалуйста, введите продукты, например: курица, рис, овощи")
        return WAITING_PRODUCTS

    context.user_data["products"] = [p.strip() for p in text.split(",") if p.strip()]
    await update.message.reply_text("На сколько дней вы хотите составить план?")
    return WAITING_DAYS

# Шаг 3: дни
async def process_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text)
        context.user_data["days"] = days
    except ValueError:
        await update.message.reply_text("Введите число, например 3:")
        return WAITING_DAYS

    await update.message.reply_text("Сколько приёмов пищи в день?")
    return WAITING_MEALS

# Шаг 4: приёмы пищи
async def process_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        meals = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число, например 4:")
        return WAITING_MEALS

    products = context.user_data.get("products", [])
    days = context.user_data.get("days")

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

# Показать сохранённый план
async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = await get_meal_plan(str(update.effective_user.id))
    if not plan:
        await update.message.reply_text("❌ У вас нет сохранённого плана.")
    else:
        await update.message.reply_text(f"📋 Ваш сохранённый план:\n\n{plan.plan_text}")
