# logic/keyboards/callback.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .product_button import (
    category_menu,
    product_keyboards,
    get_product_name,
    next_step_keyboard,
)

from logic.gigachat import assess_and_plan  # async-функция


def _ensure_cart(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Гарантируем, что корзина существует и не перетирается."""
    context.user_data.setdefault("ingredients", [])
    # step намеренно не трогаем здесь


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


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

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

    elif data == "view_plan":
        await query.message.reply_text("Пока планов нет.")

    elif data == "saved_recipes":
        await query.message.reply_text("Сохраненных рецептов пока нет.")

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

    # 📅 План на «посильные» дни (когда не хватало на полный срок)
    elif data == "use_feasible_days":
        res = context.user_data.get("assessment")
        if res and res.get("plan_markdown"):
            await query.message.reply_text(res["plan_markdown"])
        else:
            # На всякий случай пересчитаем, если состояние потерялось
            _ensure_cart(context)
            ingredients = context.user_data.get("ingredients", [])
            days = int(context.user_data.get("days", 1))
            meals = int(context.user_data.get("meals", 3))
            new_res = await assess_and_plan(ingredients, days, meals)
            feasible = int(new_res.get("feasible_days_without_purchases", 0))
            plan_md = (new_res.get("plan_markdown") or "").strip()
            if feasible >= 1 and plan_md:
                context.user_data["assessment"] = new_res
                await query.message.reply_text(plan_md)
            else:
                await query.message.reply_text(
                    "Не удалось получить план. Добавьте продукты и попробуйте ещё раз."
                )


async def handle_grams_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    step = context.user_data.get("step")

    # 1) Ввод числа дней
    if step == "waiting_for_days":
        try:
            days = int(user_input)
            context.user_data["days"] = days
            context.user_data["step"] = "waiting_for_meals"
            await update.message.reply_text("Сколько приёмов пищи в день?")
        except ValueError:
            await update.message.reply_text("Введите корректное число дней.")
        return

    # 2) Ввод числа приёмов пищи -> оценка и план
    elif step == "waiting_for_meals":
        try:
            meals = int(user_input)
            context.user_data["meals"] = meals
            context.user_data["step"] = None

            _ensure_cart(context)
            await update.message.reply_text(
                f"Формирую план на {context.user_data['days']} дней × {meals} приёмов пищи… 🔄"
            )

            ingredients = context.user_data.get("ingredients", [])
            days = int(context.user_data.get("days"))
            meals_per_day = int(context.user_data.get("meals"))

            result = await assess_and_plan(ingredients, days, meals_per_day)

            decision = result.get("decision")
            feasible = int(result.get("feasible_days_without_purchases", 0))
            plan_md = (result.get("plan_markdown") or "").strip()
            summary = (result.get("summary_reason") or "").strip()

            if decision == "ok" or (feasible >= days and plan_md):
                await update.message.reply_text(plan_md)
                return

            if 1 <= feasible < days:
                context.user_data["assessment"] = result
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
            product = context.user_data.get("selected_product")

            if not product:
                await update.message.reply_text("Сначала выберите продукт из меню.")
                return

            _ensure_cart(context)
            ingredients = context.user_data["ingredients"]  # уже существует
            ingredients.append({"product": product, "grams": grams})

            # очищаем текущий выбор, но не корзину!
            context.user_data.pop("selected_product", None)
            context.user_data["step"] = None

            await update.message.reply_text(
                f"Продукт добавлен: {product} — {grams} г.\n"
                f"Сейчас в списке {len(ingredients)} поз.:"
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
