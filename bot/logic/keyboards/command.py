from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from logic.llm.meal_plan_generator import generate_meal_plan
from db.database import AsyncSessionLocal
from db.models import MealPlan

# ——— Состояния диалога
WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS, CONFIRM_PLAN = range(4)


# ————————————————————————————————————————————————————————
async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога — запрос списка продуктов"""
    await update.message.reply_text("Введите список доступных продуктов (через запятую):")
    return WAITING_PRODUCTS


# ————————————————————————————————————————————————————————
async def process_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь вводит продукты"""
    context.user_data["products"] = update.message.text.strip()
    await update.message.reply_text("На сколько дней составить план питания?")
    return WAITING_DAYS


# ————————————————————————————————————————————————————————
async def process_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь вводит количество дней"""
    try:
        context.user_data["days"] = int(update.message.text.strip())
        await update.message.reply_text("Сколько приёмов пищи в день?")
        return WAITING_MEALS
    except ValueError:
        await update.message.reply_text("Введите число — количество дней.")
        return WAITING_DAYS


# ————————————————————————————————————————————————————————
async def process_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь вводит количество приёмов пищи"""
    try:
        context.user_data["meals"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Введите число — количество приёмов пищи.")
        return WAITING_MEALS

    products = context.user_data["products"]
    days = context.user_data["days"]
    meals = context.user_data["meals"]

    await update.message.reply_text("⏳ Формирую план питания, подождите немного...")

    try:
        plan_text = generate_meal_plan(products, days, meals)
        context.user_data["plan_text"] = plan_text

        # 🔘 Inline-кнопки
        keyboard = [
            [
                InlineKeyboardButton("💾 Сохранить план", callback_data="save_plan"),
                InlineKeyboardButton("🔁 Пересоздать", callback_data="regen_plan"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Ваш план питания:\n\n{plan_text}",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        return CONFIRM_PLAN

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при составлении плана: {e}")
        return ConversationHandler.END


# ————————————————————————————————————————————————————————
async def handle_plan_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора: сохранить или пересоздать"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    choice = query.data
    plan_text = context.user_data.get("plan_text")

    if choice == "save_plan":
        try:
            async with AsyncSessionLocal() as session:
                plan = MealPlan(user_id=user_id, plan_text=plan_text)
                session.add(plan)
                await session.commit()

            await query.edit_message_text("✅ План питания сохранён в базе данных.")
            return ConversationHandler.END

        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка при сохранении плана: {e}")
            return ConversationHandler.END

    elif choice == "regen_plan":
        await query.edit_message_text("🔁 Хорошо, создадим новый план. Введите список продуктов:")
        return WAITING_PRODUCTS


# ————————————————————————————————————————————————————————
async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает сохранённые планы питания из базы данных"""
    user_id = update.message.from_user.id

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                MealPlan.__table__.select().where(MealPlan.user_id == user_id)
            )
            plans = result.fetchall()

        # Если у пользователя нет сохранённых планов
        if not plans:
            await update.message.reply_text("📂 У вас пока нет сохранённых планов.")
            return

        # Формируем список планов
        reply = "📋 *Ваши сохранённые планы:*\n\n"
        for i, row in enumerate(plans, start=1):
            reply += f"📅 *План {i}:*\n{row.plan_text}\n\n"

        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении данных из базы: {e}")
