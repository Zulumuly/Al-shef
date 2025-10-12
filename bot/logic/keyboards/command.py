from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db.crud import create_meal_plan, get_meal_plan
from logic.llm.meal_plan_generator import generate_meal_plan

# Состояния
PRODUCTS, DAYS, MEALS = range(3)

# Клавиатура
main_keyboard = ReplyKeyboardMarkup(
    [["Составить план питания", "Сохранённый план"]],
    resize_keyboard=True
)


# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я помогу составить персональный план питания.\n"
        "Нажми «Составить план питания», чтобы начать.",
        reply_markup=main_keyboard
    )
    return PRODUCTS


# === Обработка списка продуктов ===
async def handle_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.lower() == "составить план питания":
        await update.message.reply_text("Введите список доступных продуктов (через запятую):")
        return PRODUCTS

    context.user_data["products"] = text
    await update.message.reply_text("На сколько дней составить план питания?")
    return DAYS


# === Обработка количества дней ===
async def handle_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["days"] = update.message.text.strip()
    await update.message.reply_text("Сколько приёмов пищи в день?")
    return MEALS


# === Обработка количества приёмов пищи ===
async def handle_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    products = context.user_data.get("products")
    days = context.user_data.get("days")
    meals = update.message.text.strip()

    await update.message.reply_text("⏳ Формирую план питания, подождите немного...")

    try:
        plan_text = generate_meal_plan(products, days, meals)

        await update.message.reply_text(
            f"✅ Ваш план питания:\n\n{plan_text}\n\n"
            "Хотите сохранить план?",
            reply_markup=ReplyKeyboardMarkup(
                [["Сохранить", "Составить новый"]],
                resize_keyboard=True
            )
        )

        context.user_data["plan_text"] = plan_text
        context.user_data["days"] = days
        context.user_data["meals"] = meals
        return MEALS

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при составлении плана: {e}")
        return PRODUCTS


# === Сохранение или просмотр сохранённого плана ===
async def show_saved_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    try:
        plan = await get_meal_plan(user_id)
        if plan:
            await update.message.reply_text(f"📋 Ваш сохранённый план:\n\n{plan.plan_text}")
        else:
            await update.message.reply_text("📭 У вас пока нет сохранённых планов.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении данных из базы: {e}")
