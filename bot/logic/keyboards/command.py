from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler

from db.crud import create_meal_plan, get_meal_plan
from logic.llm.gigachat_api import ask_gigachat  
from telegram import ReplyKeyboardMarkup


# --- Состояния диалога ---
PRODUCTS, DAYS, MEALS = range(3)


# --- Главное меню ---
def main_menu_keyboard():
    keyboard = [
        ["📋 Показать сохранённый план", "🧠 Создать новый план"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# --- Стартовое сообщение ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я помогу составить план питания.\n\n"
        "Выберите действие 👇",
        reply_markup=main_menu_keyboard()
    )


# --- Создание нового плана ---
async def new_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите список продуктов (через запятую):"
    )
    return PRODUCTS


async def handle_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["products"] = update.message.text
    await update.message.reply_text("На сколько дней нужен план?")
    return DAYS


async def handle_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["days"] = update.message.text
    await update.message.reply_text("Сколько приёмов пищи в день?")
    return MEALS


async def handle_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.message.from_user.id)
    context.user_data["meals_per_day"] = update.message.text

    products = context.user_data["products"]
    days = context.user_data["days"]
    meals_per_day = context.user_data["meals_per_day"]

    await update.message.reply_text("Формирую план питания, подождите немного...")

    plan_text = ask_gigachat(
        f"Составь план питания из продуктов: {products}. "
        f"На {days} дней, {meals_per_day} приём(а) пищи в день. "
        f"Не добавляй ничего лишнего. Формат:\n"
        f"День 1:\n- Завтрак: ...\n  Рецепт: ..."
    )

    # Сохраняем результат в базу
    await create_meal_plan(
        user_id=user_id,
        products=products,
        days=days,
        meals_per_day=meals_per_day,
        plan_text=plan_text
    )

    await update.message.reply_text("✅ План питания сохранён в базе данных.")
    await update.message.reply_text(
        plan_text if plan_text else "❌ Не удалось получить план от GigaChat."
    )

    # Возвращаем меню
    await update.message.reply_text(
        "Выберите действие 👇",
        reply_markup=main_menu_keyboard()
    )

    return ConversationHandler.END


# --- Показ сохранённого плана ---
async def show_saved_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.message.from_user.id)
    plan = await get_meal_plan(user_id)

    if plan:
        await update.message.reply_text(
            f"📋 Ваш последний сохранённый план:\n\n{plan.plan_text}",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ У вас ещё нет сохранённого плана.\n"
            "Создайте новый, выбрав «🧠 Создать новый план».",
            reply_markup=main_menu_keyboard()
        )
