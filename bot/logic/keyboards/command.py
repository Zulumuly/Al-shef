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

# Состояния диалога
WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS, CONFIRM_PLAN = range(4)


# ————————————————————————————————————————————————————————
async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога — запрос списка продуктов"""
    await update.message.reply_text("Введите список доступных продуктов (через запятую):")
    return WAITING_PRODUCTS


# ————————————————————————————————————————————————————————
async def process_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["products"] = update.message.text.strip()
    await update.message.reply_text("На сколько дней составить план питания?")
    return WAITING_DAYS


# ————————————————————————————————————————————————————————
async def process_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["days"] = int(update.message.text.strip())
        await update.message.reply_text("Сколько приёмов пищи в день?")
        return WAITING_MEALS
    except ValueError:
        await update.message.reply_text("Введите число — количество дней.")
        return WAITING_DAYS


# ————————————————————————————————————————————————————————
async def process_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    """Обработка кнопок — сохранить или пересоздать"""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    choice = query.data
    plan_text = context.user_data.get("plan_text")

    if choice == "save_plan":
        try:
            async with AsyncSessionLocal() as session:
                plan = MealPlan(
                    user_id=user_id,
                    products=context.user_data.get("products"),
                    days=context.user_data.get("days"),
                    meals_per_day=context.user_data.get("meals"),
                    plan_text=plan_text,
                )
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
    message = update.message or update.callback_query.message
    user_id = str(update.effective_user.id)

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                MealPlan.__table__.select().where(MealPlan.user_id == user_id)
            )
            plans = result.fetchall()

        if not plans:
            await message.reply_text("📂 У вас пока нет сохранённых планов.")
            return

        full_text = "📋 *Ваши сохранённые планы:*\n\n"
        for i, row in enumerate(plans, start=1):
            full_text += f"📅 *План {i}:*\n{row.plan_text}\n\n"

        # Разбиваем длинный текст, чтобы избежать ошибки Telegram
        max_len = 4000
        chunks = [full_text[i:i + max_len] for i in range(0, len(full_text), max_len)]

        for chunk in chunks:
            await message.reply_text(chunk, parse_mode="Markdown")

    except Exception as e:
        await message.reply_text(f"❌ Ошибка при получении данных из базы: {e}")
