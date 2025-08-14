# logic/keyboards/callback.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from db.crud import save_plan, get_latest_plan, list_plan_summaries, get_plan_by_id

from .product_button import (
    category_menu,
    product_keyboards,
    get_product_name,
    next_step_keyboard,
)

from logic.gigachat import assess_and_plan  # async-функция


# ---------- helpers ----------

def _ensure_cart(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Гарантируем, что корзина существует и не перетирается."""
    context.user_data.setdefault("ingredients", [])


def _cart_summary(context: ContextTypes.DEFAULT_TYPE) -> str:
    items = context.user_data.get("ingredients", [])
    if not items:
        return "Пока ничего не добавлено."
    lines = []
    for it in items:
        p = it.get("product")
        g = it.get("grams")
        lines.append(f"• {p}" + (f" — {g} г" if g is not None else ""))
    return "\n".join(lines)


async def _send_long_text(message_obj, text: str) -> None:
    """Телеграм ограничивает сообщение ~4096 символами — шлём чанками ~3900."""
    chunk = 3900
    text = text or ""
    while text:
        part, text = text[:chunk], text[chunk:]
        await message_obj.reply_text(part)


async def _safe_answer(query) -> None:
    """Безопасный ответ на callback, игнорируем 'Query is too old...'."""
    try:
        await query.answer()
    except BadRequest as e:
        msg = str(e).lower()
        if "query is too old" in msg or "query id is invalid" in msg:
            return
        raise


def _post_plan_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💾 Сохранить этот план", callback_data="save_generated_plan")],
        [InlineKeyboardButton("🔁 Пересоздать план", callback_data="regenerate_plan")],
        [InlineKeyboardButton("➕ Добавить продукты", callback_data="add_more_products")]
    ])


def _store_last_plan(context: ContextTypes.DEFAULT_TYPE, *, plan_md: str, requested_days: int,
                     meals_per_day: int, feasible_days: int | None, decision: str | None,
                     ingredients: list[dict]) -> None:
    context.user_data["last_generated_plan"] = {
        "plan_md": plan_md,
        "requested_days": requested_days,
        "meals_per_day": meals_per_day,
        "feasible_days": feasible_days,
        "decision": decision,
        "ingredients": ingredients,
    }


# ---------- handlers ----------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await _safe_answer(query)
    data = query.data
    user_id = update.effective_user.id

    # 🟢 Начать (или вернуться) к выбору продуктов — НЕ очищаем корзину
    if data == "input_products":
        _ensure_cart(context)
        context.user_data.setdefault("step", None)
        await query.message.reply_text(
            "Выбери категорию продуктов:"
            f"\n— уже выбрано позиций: {len(context.user_data['ingredients'])}",
            reply_markup=category_menu
        )

    elif data.startswith("cat_"):
        _ensure_cart(context)
        keyboard = product_keyboards.get(data)
        if keyboard:
            await query.message.reply_text("Выбери продукт:", reply_markup=keyboard)

    elif data.startswith("prod_"):
        _ensure_cart(context)
        product = get_product_name(data)
        if product:
            context.user_data["selected_product"] = product
            context.user_data["step"] = "waiting_for_grams"
            await query.message.reply_text(
                f"Введите количество в граммах для продукта: {product}"
            )

    # 🔎 ПОСМОТРЕТЬ ПОСЛЕДНИЙ СОХРАНЁННЫЙ ПЛАН
    elif data == "view_plan":
        rec = await get_latest_plan(user_id)
        if not rec:
            await query.message.reply_text("Пока сохранённых планов нет.")
        else:
            await _send_long_text(query.message, rec["plan_md"])

    # 📚 СПИСОК СОХРАНЁННЫХ ПЛАНОВ
    elif data == "saved_recipes":
        items = await list_plan_summaries(user_id)
        if not items:
            await query.message.reply_text("Сохранённых планов пока нет.")
        else:
            rows = [[InlineKeyboardButton(i["title"], callback_data=f"show_plan:{i['id']}")] for i in items[:10]]
            await query.message.reply_text("Выберите план:", reply_markup=InlineKeyboardMarkup(rows))

    elif data.startswith("show_plan:"):
        plan_id = data.split(":", 1)[1]
        rec = await get_plan_by_id(user_id, plan_id)
        if not rec:
            await query.message.reply_text("План не найден.")
        else:
            await _send_long_text(query.message, rec["plan_md"])

    elif data == "back_to_categories":
        _ensure_cart(context)
        await query.message.reply_text(
            "Выбери категорию продуктов:"
            f"\n— уже выбрано позиций: {len(context.user_data['ingredients'])}",
            reply_markup=category_menu
        )

    # ➕ Добавить продукты — НЕ очищаем корзину
    elif data == "add_more_products":
        _ensure_cart(context)
        context.user_data["step"] = None
        await query.message.reply_text(
            "Выбери следующую категорию:"
            f"\n— уже выбрано позиций: {len(context.user_data['ingredients'])}",
            reply_markup=category_menu
        )

    elif data == "choose_meals_days":
        _ensure_cart(context)
        context.user_data["step"] = "waiting_for_days"
        await query.message.reply_text(
            "Сколько дней планируем питание? (Напиши число)"
        )

    # 📅 План на «посильные» дни (когда не хватало на полный срок): теперь не сохраняем авто!
    elif data == "use_feasible_days":
        res = context.user_data.get("assessment")
        if res and res.get("plan_markdown"):
            plan_md = res["plan_markdown"].strip()
            requested_days = int(res.get("requested_days") or context.user_data.get("days") or 0)
            meals_per_day = int(res.get("meals_per_day") or context.user_data.get("meals") or 0)
            feasible_days = int(res.get("feasible_days_without_purchases") or 0)
            decision = str(res.get("decision") or "reduce")
            ingredients = context.user_data.get("ingredients", [])

            _store_last_plan(
                context,
                plan_md=plan_md,
                requested_days=requested_days,
                meals_per_day=meals_per_day,
                feasible_days=feasible_days,
                decision=decision,
                ingredients=ingredients,
            )

            await _send_long_text(query.message, plan_md)
            await query.message.reply_text("Что дальше?", reply_markup=_post_plan_keyboard())
        else:
            # подстраховка
            _ensure_cart(context)
            ingredients = context.user_data.get("ingredients", [])
            days = int(context.user_data.get("days", 1))
            meals = int(context.user_data.get("meals", 3))
            new_res = await assess_and_plan(ingredients, days, meals)
            feasible = int(new_res.get("feasible_days_without_purchases", 0))
            plan_md = (new_res.get("plan_markdown") or "").strip()
            if feasible >= 1 and plan_md:
                context.user_data["assessment"] = new_res
                _store_last_plan(
                    context,
                    plan_md=plan_md,
                    requested_days=int(new_res.get("requested_days") or days),
                    meals_per_day=int(new_res.get("meals_per_day") or meals),
                    feasible_days=feasible,
                    decision=str(new_res.get("decision") or "reduce"),
                    ingredients=ingredients,
                )
                await _send_long_text(query.message, plan_md)
                await query.message.reply_text("Что дальше?", reply_markup=_post_plan_keyboard())
            else:
                await query.message.reply_text(
                    "Не удалось получить план. Добавьте продукты и попробуйте ещё раз."
                )

    # 💾 Сохранить последний сгенерированный план
    elif data == "save_generated_plan":
        last = context.user_data.get("last_generated_plan")
        if not last:
            await query.message.reply_text("Нет сгенерированного плана для сохранения.")
            return
        plan_id = await save_plan(
            user_id=user_id,
            plan_md=last["plan_md"],
            requested_days=last["requested_days"],
            meals_per_day=last["meals_per_day"],
            feasible_days=last.get("feasible_days"),
            decision=last.get("decision"),
            ingredients=last.get("ingredients") or [],
        )
        await query.message.reply_text(f"💾 План сохранён (id: {plan_id}).\n"
                                       f"Открыть: «📅 Посмотреть сохраненный план» или «📘 Сохраненные рецепты».")

    # 🔁 Пересоздать с теми же параметрами
    elif data == "regenerate_plan":
        last = context.user_data.get("last_generated_plan")
        if not last:
            # если нет last, попытаться взять из текущего стейта
            ingredients = context.user_data.get("ingredients", [])
            days = int(context.user_data.get("days", 0) or 0)
            meals = int(context.user_data.get("meals", 0) or 0)
        else:
            ingredients = last.get("ingredients", [])
            days = int(last.get("requested_days") or 0)
            meals = int(last.get("meals_per_day") or 0)

        if not ingredients or days <= 0 or meals <= 0:
            await query.message.reply_text("Не хватает данных для пересоздания. Укажи продукты и параметры заново.")
            return

        await query.message.reply_text("Пересоздаю план… 🔄")
        result = await assess_and_plan(ingredients, days, meals)
        feasible = int(result.get("feasible_days_without_purchases", 0))
        plan_md = (result.get("plan_markdown") or "").strip()
        decision = result.get("decision")

        if plan_md:
            _store_last_plan(
                context,
                plan_md=plan_md,
                requested_days=days,
                meals_per_day=meals,
                feasible_days=feasible,
                decision=str(decision or "ok"),
                ingredients=ingredients,
            )
            await _send_long_text(query.message, plan_md)
            await query.message.reply_text("Что дальше?", reply_markup=_post_plan_keyboard())
        else:
            await query.message.reply_text("Не удалось пересоздать план. Попробуй ещё раз или скорректируй продукты.")


async def handle_grams_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    step = context.user_data.get("step")
    user_id = update.effective_user.id

    # 1) Ввод числа дней
    if step == "waiting_for_days":
        try:
            days = int(user_input)
            if not 1 <= days <= 21:
                await update.message.reply_text("Укажи число дней от 1 до 21.")
                return
            context.user_data["days"] = days
            context.user_data["step"] = "waiting_for_meals"
            await update.message.reply_text("Сколько приёмов пищи в день?")
        except ValueError:
            await update.message.reply_text("Введите корректное число дней.")
        return

    # 2) Ввод числа приёмов пищи -> оценка и план (без автосохранения)
    elif step == "waiting_for_meals":
        try:
            meals = int(user_input)
            if not 1 <= meals <= 6:
                await update.message.reply_text("Укажи число приёмов пищи от 1 до 6.")
                return

            context.user_data["meals"] = meals
            context.user_data["step"] = None

            _ensure_cart(context)
            await update.message.reply_text(
             f"Подбираю рецепты на {context.user_data['days']} дней × {meals} приёмов… 🔎🍳"
                )

            ingredients = context.user_data.get("ingredients", [])
            days = int(context.user_data.get("days"))
            meals_per_day = int(context.user_data.get("meals"))

            result = await assess_and_plan(ingredients, days, meals_per_day)

            decision = result.get("decision")
            feasible = int(result.get("feasible_days_without_purchases", 0))
            plan_md = (result.get("plan_markdown") or "").strip()
            summary = (result.get("summary_reason") or "").strip()

            # хватает — просто показываем план и предлагаем действия
            if (decision == "ok" or feasible >= days) and plan_md:
                _store_last_plan(
                    context,
                    plan_md=plan_md,
                    requested_days=days,
                    meals_per_day=meals_per_day,
                    feasible_days=feasible,
                    decision=str(decision or "ok"),
                    ingredients=ingredients,
                )
                await _send_long_text(update.message, plan_md)
                await update.message.reply_text("Что дальше?", reply_markup=_post_plan_keyboard())
                return

            # не хватает — предлагаем план на посильные дни или добавить продукты
            if 1 <= feasible < days and plan_md:
                context.user_data["assessment"] = result
                _store_last_plan(
                    context,
                    plan_md=plan_md,
                    requested_days=days,
                    meals_per_day=meals_per_day,
                    feasible_days=feasible,
                    decision=str(decision or "reduce"),
                    ingredients=ingredients,
                )
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"📅 План на {feasible} дней", callback_data="use_feasible_days")],
                    [InlineKeyboardButton("➕ Добавить продукты", callback_data="add_more_products")],
                ])
                text = (
                    f"Текущих продуктов хватает примерно на {feasible} дн. "
                    f"(запрошено: {days})."
                )
                if summary:
                    text += f"\n{summary}"
                await update.message.reply_text(text, reply_markup=kb)
                return

            # совсем не хватает
            await update.message.reply_text(
                "Текущих продуктов недостаточно даже на 1 день.\n\n"
                "Сейчас в списке:\n"
                f"{_cart_summary(context)}\n\n"
                "Добавьте продукты и попробуем снова.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Добавить продукты", callback_data="add_more_products")]
                ])
            )
            return

        except ValueError:
            await update.message.reply_text("Введите корректное число приёмов пищи.")
        return

    # 3) Ввод граммов для выбранного продукта
    elif step == "waiting_for_grams":
        try:
            grams = int(user_input)
            if not 1 <= grams <= 5000:
                await update.message.reply_text("Введи граммы от 1 до 5000.")
                return

            product = context.user_data.get("selected_product")
            if not product:
                await update.message.reply_text("Сначала выберите продукт из меню.")
                return

            _ensure_cart(context)
            context.user_data["ingredients"].append({"product": product, "grams": grams})

            # очищаем текущий выбор, но не корзину!
            context.user_data.pop("selected_product", None)
            context.user_data["step"] = None

            await update.message.reply_text(
                f"Продукт добавлен: {product} — {grams} г.\n"
                f"Сейчас в списке {len(context.user_data['ingredients'])} поз.:"
                f"\n{_cart_summary(context)}\n\nЧто дальше?",
                reply_markup=next_step_keyboard
            )
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число (в граммах).")
        return

    # Если шаг неизвестен — не сбрасываем корзину, а возвращаемся к категориям
    _ensure_cart(context)
    await update.message.reply_text(
        "Сначала выберите продукт из меню:"
        f"\n— уже выбрано позиций: {len(context.user_data['ingredients'])}",
        reply_markup=category_menu
    )
