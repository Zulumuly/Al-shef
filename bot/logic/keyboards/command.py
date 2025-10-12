from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from logic.llm.meal_plan_generator import generate_meal_plan
from db.database import AsyncSessionLocal
from db.models import MealPlan

WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS, CONFIRM_PLAN = range(4)

# ——————————————————————————————————————————————
async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите список доступных продуктов (через запятую):")
    return WAITING_PRODUCTS


async def process_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["products"] = update.message.text
    await update.message.reply_text("На сколько дней составить план?")
    return WAITING_DAYS


async def process_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["days"] = int(update.message.text)
    await update.message.reply_text("Сколько приёмов пищи в день?")
    return WAITING_MEALS


async def process_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["meals"] = int(update.message.text)

    products = context.user_data["products"]
    days = context.user_data["days"]
    meals = context.user_data["meals"]

    await update.message.reply_text("⏳ Формирую план питания, подождите немного...")

    try:
        plan_text = generate_meal_plan(products, days, meals)
        context.user_data["plan_text"] = plan_text

        # Кнопки "Сохранить" / "Пересоздать"
        keyboard = [
            [
                InlineKeyboardButton("💾 Сохранить план", callback_data="save_plan"),
                InlineKeyboardButton("🔁 Пересоздать", callback_data="regen_plan"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(f"✅ Ваш план питания:\n\n{plan_text}", reply_markup=reply_markup)
        return CONFIRM_PLAN

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при составлении плана: {e}")
        return ConversationHandler.END


# ——————————————————————————————————————————————
async def handle_plan_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок 'Сохранить' и 'Пересоздать'"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    choice = query.data
    plan_text = context.user_data.get("plan_text")

    if choice == "save_plan":
        async with AsyncSessionLocal() as session:
            plan = MealPlan(user_id=user_id, plan_text=plan_text)
            session.add(plan)
            await session.commit()

        await query.edit_message_text("✅ План питания сохранён в базе данных.")
        return ConversationHandler.END

    elif choice == "regen_plan":
        await query.edit_message_text("🔁 Хорошо, давайте пересоздадим план. Введите список продуктов заново:")
        return WAITING_PRODUCTS
