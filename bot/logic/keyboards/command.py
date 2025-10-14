from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from db.crud import create_meal_plan, get_meal_plan
from logic.llm.gigachat_api import ask_gigachat

ASK_PRODUCTS, ASK_DAYS, ASK_MEALS = range(3)


# --- Главное меню (только при /start) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Я помогу тебе составить персональный план питания.\n\n"
        "Используй меню слева:\n"
        "🧠 /plan — создать новый план\n"
        "📋 /saved — посмотреть сохранённые планы."
    )


# --- Новый план ---
async def new_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите продукты, которые вы хотите включить в рацион (через запятую):",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_PRODUCTS


# --- Шаг 1: продукты ---
async def handle_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["products"] = update.message.text
    await update.message.reply_text("На сколько дней нужен план?")
    return ASK_DAYS


# --- Шаг 2: дни ---
async def handle_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["days"] = update.message.text
    await update.message.reply_text("Сколько приёмов пищи в день?")
    return ASK_MEALS


# --- Шаг 3: приёмы пищи ---
async def handle_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.message.from_user.id)
    products = context.user_data.get("products")
    days = update.message.text if context.user_data.get("days") is None else context.user_data["days"]
    meals_per_day = update.message.text

    await update.message.reply_text("Формирую план питания, подождите немного...")

    prompt = (
        f"Составь план питания на {days} дней с {meals_per_day} приёмами пищи в день "
        f"на основе следующих продуктов: {products}. "
        "Укажи блюда и примерное описание по дням."
    )

    plan_text = ask_gigachat(prompt)

    # ✅ Сохраняем всё в context.user_data, чтобы inline-кнопки имели доступ
    context.user_data.update({
        "plan_text": plan_text,
        "days": days,
        "meals_per_day": meals_per_day,
        "products": products,
    })

    buttons = [
        [
            InlineKeyboardButton("💾 Сохранить план", callback_data="save_plan"),
            InlineKeyboardButton("🔄 Создать новый", callback_data="new_plan"),
        ]
    ]

    await update.message.reply_text(plan_text)
    await update.message.reply_text(
        "Что вы хотите сделать дальше?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    return ConversationHandler.END


# --- Сохранение плана ---
async def handle_save_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.from_user.id)
    products = context.user_data.get("products", "")
    days = int(context.user_data.get("days", "1"))
    meals_per_day = int(context.user_data.get("meals_per_day", "3"))
    plan_text = context.user_data.get("plan_text", "")

    if not plan_text:
        await query.edit_message_text("❌ Ошибка: нет данных для сохранения.")
        return

    await create_meal_plan(user_id, products, days, meals_per_day, plan_text)
    await query.edit_message_text("✅ План питания сохранён! Чтобы посмотреть, открой меню → 📋 Saved.")


# --- Пересоздание плана ---
async def handle_new_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "Введите продукты для нового плана:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_PRODUCTS


# --- Просмотр сохранённого плана ---
async def show_saved_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.message.from_user.id)
    plan = await get_meal_plan(user_id)

    if plan:
        await update.message.reply_text(
            f"📋 Ваш сохранённый план питания:\n\n{plan.plan_text}"
        )
    else:
        await update.message.reply_text("❌ У вас пока нет сохранённого плана.")
