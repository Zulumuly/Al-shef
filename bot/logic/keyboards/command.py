from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update

from telegram.ext import ContextTypes, ConversationHandler

from db.crud import create_meal_plan, get_meal_plan
from logic.llm.gigachat_api import ask_gigachat  
from telegram import ReplyKeyboardMarkup


# --- Состояния диалога ---
ASK_PRODUCTS, ASK_DAYS, ASK_MEALS = range(3)

# --- Главное меню ---
def main_menu_keyboard():
    keyboard = [
        ["🧠 Создать новый план"],
        ["📋 Показать сохранённый план"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Кнопки после генерации плана ---
def after_plan_keyboard():
    keyboard = [
        ["✅ Сохранить план", "🔁 Создать новый план"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# --- Старт / Главное меню ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Я помогу тебе составить персональный план питания.\n\n"
        "Выбери действие ниже 👇",
        reply_markup=main_menu_keyboard()
    )


# --- Начало создания нового плана ---
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
    days = context.user_data.get("days")
    meals_per_day = context.user_data.get("meals_per_day", update.message.text)

    await update.message.reply_text("Формирую план питания, подождите немного...")

    prompt = (
        f"Составь план питания на {days} дней с {meals_per_day} приёмами пищи в день "
        f"на основе следующих продуктов: {products}. "
        "Укажи блюда и примерное описание по дням."
    )

    plan_text = ask_gigachat(prompt)

    # сохраняем текст во временные данные пользователя
    context.user_data["plan_text"] = plan_text

    await update.message.reply_text(plan_text)
    await update.message.reply_text(
        "Что вы хотите сделать дальше?",
        reply_markup=after_plan_keyboard()
    )

    return ConversationHandler.END


# --- Сохранить план ---
async def handle_save_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.message.from_user.id)
    products = context.user_data.get("products", "")
    days = int(context.user_data.get("days", "1"))
    meals_per_day = int(context.user_data.get("meals_per_day", "3"))
    plan_text = context.user_data.get("plan_text", "")

    await create_meal_plan(user_id, products, days, meals_per_day, plan_text)

    await update.message.reply_text(
        "✅ План питания сохранён в базе данных.",
        reply_markup=main_menu_keyboard()
    )


# --- Создать новый план (сразу пересоздание) ---
async def handle_new_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите продукты для нового плана:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_PRODUCTS


# --- Показать сохранённый план ---
async def show_saved_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.message.from_user.id)
    plan = await get_meal_plan(user_id)

    if plan:
        await update.message.reply_text(
            f"📋 Ваш сохранённый план питания:\n\n{plan.plan_text}",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ У вас пока нет сохранённого плана.",
            reply_markup=main_menu_keyboard()
        )
