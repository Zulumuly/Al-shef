# logic/keyboards/callback.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from db.crud import save_plan, get_latest_plan, list_plan_summaries, get_plan_by_id
from logic.gigachat import assess_and_plan  


# ---------- helpers ----------

def _ensure_cart(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Гарантируем, что корзина существует."""
    if "ingredients" not in context.user_data:
        context.user_data["ingredients"] = []


def _cart_summary(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Возвращает текстовое описание корзины."""
    items = context.user_data.get("ingredients", [])
    if not items:
        return "🛒 Пока ничего не добавлено."
    
    lines = []
    for it in items:
        p = it.get("product")
        g = it.get("grams")
        lines.append(f"• {p}" + (f" — {g} г" if g is not None else ""))
    return "\n".join(lines)


async def _send_long_text(message_obj, text: str, max_length: int = 3900) -> None:
    """Отправляет длинный текст по частям с улучшенной логикой разбивки."""
    if not text:
        await message_obj.reply_text("❌ Текст пуст")
        return
    
    # Разбиваем на части, сохраняя целостность абзацев
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk:
                await message_obj.reply_text(current_chunk.strip())
                current_chunk = paragraph
            else:
                # Если один абзац слишком длинный, разбиваем принудительно
                for i in range(0, len(paragraph), max_length):
                    await message_obj.reply_text(paragraph[i:i+max_length])
        else:
            if current_chunk:
                current_chunk += '\n\n' + paragraph
            else:
                current_chunk = paragraph
    
    if current_chunk:
        await message_obj.reply_text(current_chunk.strip())


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
    """Клавиатура после генерации плана."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💾 Сохранить этот план", callback_data="save_generated_plan")],
        [InlineKeyboardButton("🔁 Пересоздать план", callback_data="regenerate_plan")],
        [InlineKeyboardButton("✏️ Изменить список продуктов", callback_data="edit_products")]
    ])


def _store_last_plan(context: ContextTypes.DEFAULT_TYPE, *, plan_md: str, requested_days: int,
                     meals_per_day: int, feasible_days: int | None, decision: str | None,
                     ingredients: list[dict]) -> None:
    """Сохраняет последний сгенерированный план в user_data."""
    context.user_data["last_generated_plan"] = {
        "plan_md": plan_md,
        "requested_days": requested_days,
        "meals_per_day": meals_per_day,
        "feasible_days": feasible_days,
        "decision": decision,
        "ingredients": ingredients.copy() if ingredients else [],
    }


def _validate_positive_int(value: str, min_val: int = 1, max_val: int = 10000) -> int | None:
    """Проверяет и преобразует строку в положительное число."""
    try:
        num = int(value)
        if min_val <= num <= max_val:
            return num
        return None
    except (ValueError, TypeError):
        return None


def _parse_products_input(text: str) -> list[dict]:
    """
    Парсит ввод пользователя в список продуктов.
    Формат: продукт количество г
    Пример: курица 500 г\nрис 200 г\nпомидоры 300 г
    """
    products = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('•'):
            continue
            
        # Убираем маркеры списка если есть
        line = line.replace('•', '').replace('-', '').strip()
        
        # Парсим продукт и количество
        parts = line.split()
        if len(parts) < 2:
            continue
            
        # Ищем число (количество)
        quantity = None
        product_parts = []
        
        for part in parts:
            if part.isdigit():
                quantity = int(part)
            else:
                # Пропускаем "г", "грамм" и т.д.
                if part.lower() not in ['г', 'грамм', 'граммов', 'g']:
                    product_parts.append(part)
        
        if product_parts and quantity:
            product_name = ' '.join(product_parts).strip()
            products.append({
                "product": product_name,
                "grams": quantity
            })
    
    return products


# ---------- handlers ----------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик callback-запросов."""
    query = update.callback_query
    await _safe_answer(query)
    data = query.data
    user_id = update.effective_user.id

    # ✏️ Редактировать список продуктов
    if data == "edit_products":
        context.user_data["step"] = "waiting_for_products"
        await query.edit_message_text(
            "📝 Введите новый список продуктов и их количество (в граммах):\n\n"
            "Например:\n"
            "курица 500 г\n"
            "рис 200 г\n"
            "помидоры 300 г\n\n"
            "Я очищу текущий список и заменю его на новый."
        )

    # 🔎 ПОСМОТРЕТЬ ПОСЛЕДНИЙ СОХРАНЁННЫЙ ПЛАН
    elif data == "view_plan":
        rec = await get_latest_plan(user_id)
        if not rec:
            await query.edit_message_text("📭 Пока сохранённых планов нет.")
        else:
            await query.edit_message_text("📋 Ваш последний сохранённый план:")
            await _send_long_text(query.message, rec["plan_md"])

    # 📚 СПИСОК СОХРАНЁННЫХ ПЛАНОВ
    elif data == "saved_recipes":
        items = await list_plan_summaries(user_id)
        if not items:
            await query.edit_message_text("📭 Сохранённых планов пока нет.")
        else:
            rows = [[InlineKeyboardButton(
                f"📋 {i['title']}", 
                callback_data=f"show_plan:{i['id']}"
            )] for i in items[:10]]
            
            await query.edit_message_text(
                f"📚 Ваши сохранённые планы ({len(items)}):",
                reply_markup=InlineKeyboardMarkup(rows)
            )

    elif data.startswith("show_plan:"):
        plan_id = data.split(":", 1)[1]
        rec = await get_plan_by_id(user_id, plan_id)
        if not rec:
            await query.edit_message_text("❌ План не найден.")
        else:
            await query.edit_message_text("📋 Ваш сохранённый план:")
            await _send_long_text(query.message, rec["plan_md"])

    # 📅 ВВОД ПАРАМЕТРОВ ДЛЯ ПЛАНА
    elif data == "choose_meals_days":
        _ensure_cart(context)
        ingredients = context.user_data.get("ingredients", [])
        if not ingredients:
            await query.edit_message_text(
                "❌ Сначала добавьте продукты! Используйте команду /plan для ввода списка продуктов.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Ввести продукты", callback_data="edit_products")]
                ])
            )
            return
            
        context.user_data["step"] = "waiting_for_days"
        await query.edit_message_text(
            "📅 На сколько дней планируем питание? (Введите число от 1 до 21)"
        )

    # 📅 План на посильные дни
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

            await query.edit_message_text(f"🍽️ План на {feasible_days} дней:")
            await _send_long_text(query.message, plan_md)
            await query.message.reply_text("Что дальше?", reply_markup=_post_plan_keyboard())
        else:
            # Резервный вариант
            _ensure_cart(context)
            ingredients = context.user_data.get("ingredients", [])
            days = context.user_data.get("days", 1)
            meals = context.user_data.get("meals", 3)
            
            if not ingredients:
                await query.edit_message_text(
                    "❌ Нет данных для создания плана. Добавьте продукты.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✏️ Ввести продукты", callback_data="edit_products")]
                    ])
                )
                return
                
            await query.edit_message_text("🔄 Создаю план...")
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
                await query.edit_message_text(f"🍽️ План на {feasible} дней:")
                await _send_long_text(query.message, plan_md)
                await query.message.reply_text("Что дальше?", reply_markup=_post_plan_keyboard())
            else:
                await query.edit_message_text(
                    "❌ Не удалось получить план. Добавьте продукты и попробуйте ещё раз.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✏️ Ввести продукты", callback_data="edit_products")]
                    ])
                )

    # 💾 Сохранить последний сгенерированный план
    elif data == "save_generated_plan":
        last = context.user_data.get("last_generated_plan")
        if not last:
            await query.edit_message_text("❌ Нет сгенерированного плана для сохранения.")
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
        await query.edit_message_text(
            f"💾 План успешно сохранён!\n"
            f"📋 Для просмотра используйте «Сохранённые планы»"
        )

    # 🔁 Пересоздать с теми же параметрами
    elif data == "regenerate_plan":
        last = context.user_data.get("last_generated_plan")
        if not last:
            # Попытка использовать текущие данные
            ingredients = context.user_data.get("ingredients", [])
            days = context.user_data.get("days", 0)
            meals = context.user_data.get("meals", 0)
        else:
            ingredients = last.get("ingredients", [])
            days = last.get("requested_days", 0)
            meals = last.get("meals_per_day", 0)

        if not ingredients or days <= 0 or meals <= 0:
            await query.edit_message_text(
                "❌ Не хватает данных для пересоздания. Укажите продукты и параметры заново.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Ввести продукты", callback_data="edit_products")]
                ])
            )
            return

        await query.edit_message_text("🔄 Пересоздаю план...")
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
            await query.edit_message_text(f"🍽️ Обновлённый план на {days} дней:")
            await _send_long_text(query.message, plan_md)
            await query.message.reply_text("Что дальше?", reply_markup=_post_plan_keyboard())
        else:
            await query.edit_message_text(
                "❌ Не удалось пересоздать план. Попробуйте ещё раз или измените список продуктов.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Изменить продукты", callback_data="edit_products")]
                ])
            )


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстового ввода (продукты, дни, приёмы пищи)."""
    user_input = update.message.text.strip()
    step = context.user_data.get("step")
    user_id = update.effective_user.id

    # 1) Ввод списка продуктов
    if step == "waiting_for_products":
        products = _parse_products_input(user_input)
        
        if not products:
            await update.message.reply_text(
                "❌ Не удалось распознать продукты. Пожалуйста, введите в формате:\n\n"
                "продукт количество г\n"
                "например:\n"
                "курица 500 г\n"
                "рис 200 г\n"
                "помидоры 300 г"
            )
            return
        
        # Сохраняем продукты
        _ensure_cart(context)
        context.user_data["ingredients"] = products
        context.user_data["step"] = None
        
        await update.message.reply_text(
            f"✅ Список продуктов сохранён! Добавлено {len(products)} позиций:\n\n"
            f"{_cart_summary(context)}\n\n"
            "Теперь укажите параметры для плана питания:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📅 Указать дни и приёмы пищи", callback_data="choose_meals_days")]
            ])
        )

    # 2) Ввод числа дней
    elif step == "waiting_for_days":
        days = _validate_positive_int(user_input, 1, 21)
        if days is None:
            await update.message.reply_text("❌ Введите корректное число дней от 1 до 21.")
            return
            
        context.user_data["days"] = days
        context.user_data["step"] = "waiting_for_meals"
        await update.message.reply_text("🍽️ Сколько приёмов пищи в день? (Введите число от 1 до 6)")

    # 3) Ввод числа приёмов пищи
    elif step == "waiting_for_meals":
        meals = _validate_positive_int(user_input, 1, 6)
        if meals is None:
            await update.message.reply_text("❌ Введите корректное число приёмов пищи от 1 до 6.")
            return

        context.user_data["meals"] = meals
        context.user_data["step"] = None

        _ensure_cart(context)
        ingredients = context.user_data.get("ingredients", [])
        days = context.user_data["days"]
        
        if not ingredients:
            await update.message.reply_text(
                "❌ Сначала добавьте продукты! Используйте команду /plan",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Ввести продукты", callback_data="edit_products")]
                ])
            )
            return

        await update.message.reply_text(
            f"🔍 Подбираю рецепты на {days} дней × {meals} приёмов пищи..."
        )

        try:
            result = await assess_and_plan(ingredients, days, meals)
            
            decision = result.get("decision")
            feasible = int(result.get("feasible_days_without_purchases", 0))
            plan_md = (result.get("plan_markdown") or "").strip()
            summary = (result.get("summary_reason") or "").strip()

            # Хватает продуктов
            if (decision == "ok" or feasible >= days) and plan_md:
                _store_last_plan(
                    context,
                    plan_md=plan_md,
                    requested_days=days,
                    meals_per_day=meals,
                    feasible_days=feasible,
                    decision=str(decision or "ok"),
                    ingredients=ingredients,
                )
                await update.message.reply_text(f"🍽️ План на {days} дней:")
                await _send_long_text(update.message, plan_md)
                await update.message.reply_text("Что дальше?", reply_markup=_post_plan_keyboard())
                return

            # Не хватает, но есть посильный вариант
            if 1 <= feasible < days and plan_md:
                context.user_data["assessment"] = result
                _store_last_plan(
                    context,
                    plan_md=plan_md,
                    requested_days=days,
                    meals_per_day=meals,
                    feasible_days=feasible,
                    decision=str(decision or "reduce"),
                    ingredients=ingredients,
                )
                
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"📅 План на {feasible} дней", callback_data="use_feasible_days")],
                    [InlineKeyboardButton("✏️ Изменить список продуктов", callback_data="edit_products")],
                ])
                
                text = (
                    f"⚠️ Текущих продуктов хватает примерно на {feasible} дней "
                    f"(запрошено: {days})."
                )
                if summary:
                    text += f"\n\n{summary}"
                    
                await update.message.reply_text(text, reply_markup=kb)
                return

            # Совсем не хватает
            await update.message.reply_text(
                "❌ Текущих продуктов недостаточно даже на 1 день.\n\n"
                f"🛒 Сейчас в списке:\n{_cart_summary(context)}\n\n"
                "Добавьте больше продуктов и попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Изменить список продуктов", callback_data="edit_products")]
                ])
            )

        except Exception as e:
            await update.message.reply_text(
                "❌ Произошла ошибка при создании плана. Попробуйте позже."
            )
            # Логирование ошибки
            print(f"Error in assess_and_plan: {e}")

    # Неизвестный шаг - предлагаем ввести продукты
    else:
        await update.message.reply_text(
            "🍽️ Для создания плана питания сначала введите список продуктов.\n\n"
            "Используйте команду /plan или кнопку ниже:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Ввести список продуктов", callback_data="edit_products")]
            ])
        )