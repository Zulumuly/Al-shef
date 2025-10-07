# bot/logic/commands.py
from __future__ import annotations
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.crud import get_latest_plan, list_plan_summaries

async def _send_long_text(message_obj, text: str) -> None:
    """Отправляет длинный текст по частям (чтобы не превышать лимит Telegram)."""
    chunk = 3900
    text = text or ""
    for i in range(0, len(text), chunk):
        await message_obj.reply_text(text[i:i+chunk])

# /start — пользователь вводит список продуктов (раньше было /plan)
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите список продуктов и их количество (в граммах):\n\n"
        "Например:\n"
        "• курица 500 г\n"
        "• рис 200 г\n"
        "• помидоры 300 г\n\n"
        "После этого я подберу рецепты и составлю план питания 🍽"
    )
    context.user_data["awaiting_ingredients"] = True

# /saved — показать последний сохранённый план
async def cmd_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rec = await get_latest_plan(update.effective_user.id)
    if not rec:
        await update.message.reply_text("📂 Пока сохранённых планов нет.")
    else:
        await _send_long_text(update.message, rec["plan_md"])

# /like — список сохранённых рецептов (аналогично планам)
async def cmd_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = await list_plan_summaries(update.effective_user.id)
    if not items:
        await update.message.reply_text("❤️ Сохранённых рецептов пока нет.")
        return
    rows = [
        [InlineKeyboardButton(f"📋 {i['title']}", callback_data=f"show_plan:{i['id']}")]
        for i in items[:10]
    ]
    await update.message.reply_text("Ваши сохранённые рецепты:", reply_markup=InlineKeyboardMarkup(rows))
