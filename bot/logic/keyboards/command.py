from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from logic.llm.meal_plan_generator import generate_meal_plan
from db.crud import save_meal_plan, get_last_meal_plan
from config import GIGACHAT_TOKEN

# 🔹 Состояния диалога
WAITING_PRODUCTS, WAITING_DAYS, WAITING_MEALS, CONFIRM_PLAN = range(4)


# === Этап 1: начало ===
async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск процесса планирования"""
    await update.message.reply_text("Введите список доступных продуктов (через запятую):")
    return WAITING_PRODUCTS


# === Этап 2: ввод продуктов ===
async def process_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь вводит продукты"""
    context.user_data["products"] = update.message.text
    await update.message.reply_text("На сколько дней составить план питания?")
    return WAITING_DAYS


# === Этап 3: ввод количества дней ===
async def process_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь вводит количество дней"""
    context.user_data["days"] = update.message.text
    await update.message.reply_text("Сколько приёмов пищи в день?")
    return WAITING_MEALS


# === Этап 4: ввод количества приёмов пищи ===
async def process_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь вводит количество приёмов пищи"""
    context.user_data["meals"] = update.message.text

    products = context.user_data.get("products")
    days = context.user_data.get("days")
    meals = context.user_data.get("meals")

    await update.message.reply_text("⏳ Формирую план питания, подождите немного...")

    try:
        plan_text = generate_meal_plan(products, days, meals)

        if not plan_text or "Ошибка" in plan_text:
            await update.message.reply_text("❌ Не удалось сгенерировать план. Попробуйте снова позже.")
            return ConversationHandler.END

        context.user_data["plan_text"] = plan_text

        # Кнопки “Сохранить” и “Пересоздать”
        buttons = [
            [
                InlineKeyboardButton("💾 Сохранить", callback_data="save_plan"),
                InlineKeyboardButton("🔁 Пересоздать", callback_data="regenerate_plan"),
            ]
        ]

        await update.message.reply_text(
            f"✅ Ваш план питания:\n\n{plan_text}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

        return CONFIRM_PLAN

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при составлении плана: {e}")
        return ConversationHandler.END


# === Этап 5: выбор действия (сохранить или пересоздать) ===
async def handle_plan_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок сохранить / пересоздать"""
    query = update.callback_query
    await query.answer()

    choice = query.data
    user_id = str(query.from_user.id)
    plan_text = context.user_data.get("plan_text")

    if choice == "save_plan":
        try:
            await save_meal_plan(
                user_id=user_id,
                products=context.user_data.get("products"),
                days=context.user_data.get("days"),
                meals_per_day=context.user_data.get("meals"),
                plan_text=plan_text,
            )
            await query.edit_message_text("✅ План питания сохранён в базе данных.")
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка при сохранении плана: {e}")

    elif choice == "regenerate_plan":
        await query.edit_message_text("🔄 Хорошо, давайте создадим новый план.")
        return await plan_start(update, context)

    return ConversationHandler.END


# === Этап 6: показать сохранённый план ===
async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вывести сохранённый план из БД"""
    user_id = str(update.message.from_user.id)
    try:
        plan = await get_last_meal_plan(user_id)
        if not plan:
            await update.message.reply_text(
                "📂 У вас пока нет сохранённых планов.\n\n"
                "Нажмите /plan, чтобы составить новый 🍽️"
            )
        else:
            # Если текст слишком длинный — делим на части
            chunks = [plan.plan_text[i:i + 3500] for i in range(0, len(plan.plan_text), 3500)]
            await update.message.reply_text("📋 Ваш сохранённый план:\n")
            for part in chunks:
                await update.message.reply_text(part)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении данных из базы: {e}")
