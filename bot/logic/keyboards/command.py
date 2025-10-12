from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler

from db.crud import create_meal_plan, get_meal_plan
from logic.gigachat_api import ask_gigachat   # ✅ исправленный импорт


# --- Состояния диалога ---
ASK_PRODUCTS, ASK_DAYS, ASK_MEALS = range(3)


# --- Старт ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🍽️ Составить план", callback_data="create_plan")],
        [InlineKeyboardButton("📋 Показать сохранённый", callback_data="show_saved")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Я помогу составить персональный план питания.\nВыберите действие:",
        reply_markup=reply_markup,
    )


# --- Начало создания плана ---
async def handle_start_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 Введите список продуктов, которые вы хотите использовать:")
    return ASK_PRODUCTS


# --- Продукты ---
async def handle_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["products"] = update.message.text
    await update.message.reply_text("📅 На сколько дней нужен план?")
    return ASK_DAYS


# --- Дни ---
async def handle_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["days"] = update.message.text
    await update.message.reply_text("🍴 Сколько приёмов пищи в день?")
    return ASK_MEALS


# --- Приёмы пищи + генерация плана ---
async def handle_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.message.from_user.id)
    meals_per_day = update.message.text.strip()
    products = context.user_data.get("products")
    days = context.user_data.get("days")

    await update.message.reply_text("🍳 Формирую план питания, подождите немного...")

    prompt = f"""
Ты — нутриционист. Составь план питания строго из списка продуктов ниже:
{products}

Условия:
- План должен быть на {days} дней и {meals_per_day} приём пищи(ей) в день.
- В рецептах нельзя использовать ничего, кроме указанных продуктов.
- Формат вывода:

День 1:
- Завтрак: ...
  Рецепт: ...

День 2:
- ...
"""

    plan_text = ask_gigachat(prompt)

    # Отправляем результат
    await update.message.reply_text(f"✅ План питания сформирован:\n\n{plan_text}")

    # Сохраняем в базу
    await create_meal_plan(user_id, products, days, meals_per_day, plan_text)

    # Inline-кнопки
    keyboard = [
        [InlineKeyboardButton("💾 Сохранить план", callback_data="save_plan")],
        [InlineKeyboardButton("🔁 Составить заново", callback_data="new_plan")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Хотите сохранить этот план или составить новый?",
        reply_markup=reply_markup,
    )

    return ConversationHandler.END


# --- Callback: Сохранить ---
async def handle_save_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ План сохранён! Можете вернуться к основному меню.")


# --- Callback: Новый план ---
async def handle_new_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🆕 Хорошо! Введите список продуктов для нового плана.")
    return ASK_PRODUCTS


# --- Callback: Показать сохранённый ---
async def show_saved_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.from_user.id)
    plan = await get_meal_plan(user_id)

    if plan:
        await query.edit_message_text(f"📋 Ваш сохранённый план:\n\n{plan.plan_text}")
    else:
        await query.edit_message_text("❌ У вас пока нет сохранённого плана.")
