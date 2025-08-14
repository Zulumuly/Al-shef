# logic/commands.py
from __future__ import annotations
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.crud import get_latest_plan, list_plan_summaries
from logic.keyboards.product_button import category_menu

def _ensure_cart(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.setdefault("ingredients", [])

def _cart_summary(context: ContextTypes.DEFAULT_TYPE) -> str:
    items = context.user_data.get("ingredients", [])
    if not items:
        return "Пока ничего не добавлено."
    return "\n".join(f"• {it.get('product')} — {it.get('grams')} г" for it in items)

async def _send_long_text(message_obj, text: str) -> None:
    chunk = 3900
    text = text or ""
    for i in range(0, len(text), chunk):
        await message_obj.reply_text(text[i:i+chunk])

# /plan — перейти к выбору продуктов
async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ensure_cart(context)
    context.user_data["step"] = None
    await update.message.reply_text(
        "Выбери категорию продуктов:"
        f"\n— уже выбрано позиций: {len(context.user_data['ingredients'])}",
        reply_markup=category_menu
    )

# /last — показать последний сохранённый план
async def cmd_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rec = await get_latest_plan(update.effective_user.id)
    if not rec:
        await update.message.reply_text("Пока сохранённых планов нет.")
    else:
        await _send_long_text(update.message, rec["plan_md"])

# /saved — список сохранённых планов (до 10)
async def cmd_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = await list_plan_summaries(update.effective_user.id)
    if not items:
        await update.message.reply_text("Сохранённых планов пока нет.")
        return
    rows = [[InlineKeyboardButton(i["title"], callback_data=f"show_plan:{i['id']}")] for i in items[:10]]
    await update.message.reply_text("Выберите план:", reply_markup=InlineKeyboardMarkup(rows))
