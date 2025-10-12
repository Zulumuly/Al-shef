from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from db.database import SessionLocal
from db.models import MealPlan
from logic.llm.meal_plan_generator import generate_meal_plan

# --- FSM состояния ---
WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS = range(3)


# --- План питания ---
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

    async with SessionLocal() as session:
        plan = MealPlan(
            user_id=str(update.effective_user.id),
            products=", ".join(products),
            days=days,
            meals_per_day=meals,
            plan_text=plan_text
        )
        session.add(plan)
        await session.commit()

    await update.message.reply_text(f"✅ Ваш план питания:\n\n{plan_text}")
    return ConversationHandler.END


# --- Показ сохранённого плана ---
async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        result = await session.execute(
            MealPlan.__table__.select().where(MealPlan.user_id == str(update.effective_user.id))
        )
        plan = result.first()
        if not plan:
            await update.message.reply_text("❌ У вас нет сохранённого плана.")
        else:
            await update.message.reply_text(f"📋 Ваш сохранённый план:\n\n{plan.plan_text}")


# --- Реакции на кнопки ---
async def handle_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки меню"""
    text = update.message.text.strip().lower()

    if "составить план" in text:
        return await plan_start(update, context)
    elif "сохранённый план" in text:
        return await show_saved(update, context)
    elif "избранные рецепты" in text:
        await update.message.reply_text("❤️ Раздел 'Избранное' в разработке!")
    else:
        await update.message.reply_text("Я не понимаю эту команду 😅\nПопробуйте выбрать из меню.")
