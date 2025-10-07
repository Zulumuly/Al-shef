# bot/logic/keyboards/callback.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from db.crud import save_plan, get_latest_plan, list_plan_summaries, get_plan_by_id
from logic.gigachat import assess_and_plan  


# ---------- helpers ----------

def _ensure_cart(context: ContextTypes.DEFAULT_TYPE) -> None:
    if "ingredients" not in context.user_data:
        context.user_data["ingredients"] = []


def _cart_summary(context: ContextTypes.DEFAULT_TYPE) -> str:
    items = context.user_data.get("ingredients", [])
    if not items:
        return "🛒 Пока ничего не добавлено."
    return "\n".join(
        f"• {it.get('product')}" + (f" — {it.get('grams')} г" if it.get("grams") else "")
        for it in items
    )


async def _send_long_text(message_obj, text: str, max_length: int = 3900) -> None:
    if not text:
        await message_obj.reply_text("❌ Текст пуст")
        return
    
    paragraphs = text.split('\n\n')
    current_chunk = ""
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk:
                await message_obj.reply_text(current_chunk.strip())
                current_chunk = paragraph
            else:
                for i in range(0, len(paragraph), max_length):
                    await message_obj.reply_text(paragraph[i:i+max_length])
        else:
            current_chunk = (current_chunk + '\n\n' + paragraph) if current_chunk else paragraph
    
    if current_chunk:
        await message_obj.reply_text(current_chunk.strip())


async def _safe_answer(query) -> None:
    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            return
        raise


def _post_plan_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💾 Сохранить план", callback_data="save_generated_plan")],
        [InlineKeyboardButton("🔁 Пересоздать план", callback_data="regenerate_plan")],
        [InlineKeyboardButton("✏️ Изменить продукты", callback_data="edit_products")]
    ])


def _store_last_plan(context: ContextTypes.DEFAULT_TYPE, *, plan_md: str,
                     requested_days: int, meals_per_day: int,
                     feasible_days: int | None, decision: str | None,
                     ingredients: list[dict]) -> None:
    context.user_data["last_generated_plan"] = {
        "plan_md": plan_md,
        "requested_days": requested_days,
        "meals_per_day": meals_per_day,
        "feasible_days": feasible_days,
        "decision": decision,
        "ingredients": ingredients.copy() if ingredients else [],
    }


def _validate_positive_int(value: str, min_val: int = 1, max_val: int = 10000) -> int | None:
    try:
        num = int(value)
        return num if min_val <= num <= max_val else None
    except (ValueError, TypeError):
        return None


def _parse_products_input(text: str) -> list[dict]:
    products = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.replace('•', '').replace('-', '').strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        quantity = None
        product_parts = []
        for part in parts:
            if part.isdigit():
                quantity = int(part)
            elif part.lower() not in ['г', 'грамм', 'граммов', 'g']:
                product_parts.append(part)
        if product_parts and quantity:
            products.append({"product": ' '.join(product_parts), "grams": quantity})
    return products


# ---------- handlers ----------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await _safe_answer(query)
    data = query.data
    user_id = update.effective_user.id

    # ✏️ Редактировать продукты
    if data == "edit_products":
        context.user_data["step"] = "waiting_for_products"
        await query.edit_message_text(
            "📝 Введите список продуктов и их количество (в граммах).\n\n"
            "Например:\n"
            "курица 500 г\nрис 200 г\nпомидоры 300 г\n\n"
            "Текущий список будет заменён."
        )

    # 🔎 Последний сохранённый план
    elif data == "view_plan":
        rec = await get_latest_plan(user_id)
        if not rec:
            await query.edit_message_text("📭 Пока нет сохранённых планов.")
        else:
            await query.edit_message_text("📋 Последний сохранённый план:")
            await _send_long_text(query.message, rec["plan_md"])

    # 📚 Сохранённые планы (команда /saved)
    elif data == "saved_recipes":  # переименуем позже если надо
        items = await list_plan_summaries(user_id)
        if not items:
            await query.edit_message_text("📭 Сохранённых планов пока нет.")
        else:
            rows = [[InlineKeyboardButton(f"📋 {i['title']}", callback_data=f"show_plan:{i['id']}")] for i in items[:10]]
            await query.edit_message_text("📚 Ваши сохранённые планы:", reply_markup=InlineKeyboardMarkup(rows))

    # 🔎 Просмотр конкретного сохранённого плана
    elif data.startswith("show_plan:"):
        plan_id = data.split(":", 1)[1]
        rec = await get_plan_by_id(user_id, plan_id)
        if not rec:
            await query.edit_message_text("❌ План не найден.")
        else:
            await query.edit_message_text("📋 Сохранённый план:")
            await _send_long_text(query.message, rec["plan_md"])

    # 📅 Указание параметров (дни, приёмы пищи)
    elif data == "choose_meals_days":
        _ensure_cart(context)
        if not context.user_data.get("ingredients"):
            await query.edit_message_text(
                "❌ Сначала добавьте продукты (через /start).",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✏️ Ввести продукты", callback_data="edit_products")]])
            )
            return
        context.user_data["step"] = "waiting_for_days"
        await query.edit_message_text("📅 На сколько дней нужен план? (1–21)")

    # ... остальной код handle_callback оставляем как есть ...
