from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Главное меню выбора категории продуктов
category_menu = InlineKeyboardMarkup([
    [InlineKeyboardButton("🥦 Овощи", callback_data="cat_vegetables"),
     InlineKeyboardButton("🍎 Фрукты", callback_data="cat_fruits")],
    [InlineKeyboardButton("🍖 Мясо", callback_data="cat_meat"),
     InlineKeyboardButton("🍞 Бакалея", callback_data="cat_grocery")],
    [InlineKeyboardButton("🧀 Молочное", callback_data="cat_dairy"),
     InlineKeyboardButton("🌾 Зерновое", callback_data="cat_grains")],
    [InlineKeyboardButton("🐟 Рыба и морепродукты", callback_data="cat_fish"),
     InlineKeyboardButton("🥫 Консервы", callback_data="cat_canned")],
    [InlineKeyboardButton("✅ Завершить выбор", callback_data="choose_meals_days")]
])

vegetables_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🥕 Морковь", callback_data="prod_Морковь"),
     InlineKeyboardButton("🥔 Картофель", callback_data="prod_Картофель")],
    [InlineKeyboardButton("🍅 Помидоры", callback_data="prod_Помидоры"),
     InlineKeyboardButton("🥒 Огурцы", callback_data="prod_Огурцы")],
    [InlineKeyboardButton("🧅 Лук", callback_data="prod_Лук"),
     InlineKeyboardButton("🧄 Чеснок", callback_data="prod_Чеснок")],
    [InlineKeyboardButton("🌽 Кукуруза", callback_data="prod_Кукуруза"),
     InlineKeyboardButton("🫑 Перец", callback_data="prod_Перец")],
    [InlineKeyboardButton("🥦 Брокколи", callback_data="prod_Брокколи"),
     InlineKeyboardButton("🥬 Салат", callback_data="prod_Салат")],
    [InlineKeyboardButton("🍆 Баклажан", callback_data="prod_Баклажан"),
     InlineKeyboardButton("🥒 Кабачок", callback_data="prod_Кабачок")],
    [InlineKeyboardButton("🌶 Острый перец", callback_data="prod_Острый перец"),
     InlineKeyboardButton("🫛 Горох", callback_data="prod_Горох")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

fruits_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍎 Яблоко", callback_data="prod_Яблоко"),
     InlineKeyboardButton("🍐 Груша", callback_data="prod_Груша")],
    [InlineKeyboardButton("🍊 Апельсин", callback_data="prod_Апельсин"),
     InlineKeyboardButton("🍋 Лимон", callback_data="prod_Лимон")],
    [InlineKeyboardButton("🍌 Банан", callback_data="prod_Банан"),
     InlineKeyboardButton("🍉 Арбуз", callback_data="prod_Арбуз")],
    [InlineKeyboardButton("🍇 Виноград", callback_data="prod_Виноград"),
     InlineKeyboardButton("🍒 Вишня", callback_data="prod_Вишня")],
    [InlineKeyboardButton("🍓 Клубника", callback_data="prod_Клубника"),
     InlineKeyboardButton("🫐 Черника", callback_data="prod_Черника")],
    [InlineKeyboardButton("🥭 Манго", callback_data="prod_Манго"),
     InlineKeyboardButton("🥝 Киви", callback_data="prod_Киви")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

meat_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍗 Курица", callback_data="prod_Курица"),
     InlineKeyboardButton("🥩 Говядина", callback_data="prod_Говядина")],
    [InlineKeyboardButton("🥓 Свинина", callback_data="prod_Свинина"),
     InlineKeyboardButton("🦃 Индейка", callback_data="prod_Индейка")],
    [InlineKeyboardButton("🥪 Ветчина", callback_data="prod_Ветчина"),
     InlineKeyboardButton("🌭 Сосиски", callback_data="prod_Сосиски")],
    [InlineKeyboardButton("🍖 Баранина", callback_data="prod_Баранина"),
     InlineKeyboardButton("🍖 Крольчатина", callback_data="prod_Крольчатина")],
    [InlineKeyboardButton("🥩 Печень", callback_data="prod_Печень"),
     InlineKeyboardButton("🦆 Утка", callback_data="prod_Утка")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

# Бакалея — ИСПРАВЛЕНО: все callback_data -> "prod_..."
grocery_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍚 Рис", callback_data="prod_Рис"),
     InlineKeyboardButton("🫘 Фасоль", callback_data="prod_Фасоль")],
    [InlineKeyboardButton("🧂 Соль", callback_data="prod_Соль")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

milk_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🥛 Молоко", callback_data="prod_Молоко"),
     InlineKeyboardButton("🧀 Сыр", callback_data="prod_Сыр")],
    [InlineKeyboardButton("🍦 Сливки", callback_data="prod_Сливки"),
     InlineKeyboardButton("🍶 Кефир", callback_data="prod_Кефир")],
    [InlineKeyboardButton("🥣 Йогурт", callback_data="prod_Йогурт"),
     InlineKeyboardButton("🧈 Масло", callback_data="prod_Масло")],
    [InlineKeyboardButton("🥚 Яйцо", callback_data="prod_Яйцо")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

grains_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍞 Хлеб", callback_data="prod_Хлеб"),
     InlineKeyboardButton("🍚 Рис", callback_data="prod_Рис")],
    [InlineKeyboardButton("🥣 Овсянка", callback_data="prod_Овсянка"),
     InlineKeyboardButton("🌾 Гречка", callback_data="prod_Гречка")],
    [InlineKeyboardButton("🌽 Кукурузная крупа", callback_data="prod_Кукурузная крупа"),
     InlineKeyboardButton("🍝 Макароны", callback_data="prod_Макароны")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

fish_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🐟 Лосось", callback_data="prod_Лосось"),
     InlineKeyboardButton("🐠 Тунец", callback_data="prod_Тунец")],
    [InlineKeyboardButton("🦐 Креветки", callback_data="prod_Креветки"),
     InlineKeyboardButton("🦑 Кальмары", callback_data="prod_Кальмары")],
    [InlineKeyboardButton("🐡 Треска", callback_data="prod_Треска"),
     InlineKeyboardButton("🦞 Лангуст", callback_data="prod_Лангуст")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

# Консервы
canned_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🥫 Фасоль консерв.", callback_data="prod_Фасоль консервированная"),
     InlineKeyboardButton("🥫 Кукуруза консерв.", callback_data="prod_Кукуруза консервированная")],
    [InlineKeyboardButton("🥫 Тунец консерв.", callback_data="prod_Тунец консервированный"),
     InlineKeyboardButton("🥫 Горошек консерв.", callback_data="prod_Горошек консервированный")],
    [InlineKeyboardButton("🥫 Томатная паста", callback_data="prod_Томатная паста")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

product_keyboards = {
    "cat_vegetables": vegetables_keyboard,
    "cat_fruits": fruits_keyboard,
    "cat_meat": meat_keyboard,
    "cat_dairy": milk_keyboard,
    "cat_grains": grains_keyboard,
    "cat_fish": fish_keyboard,
    "cat_canned": canned_keyboard,
    "cat_grocery": grocery_keyboard,
}

next_step_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ Добавить ещё продукт", callback_data="add_more_products")],
    [InlineKeyboardButton("➡️ Перейти к выбору приёмов пищи", callback_data="choose_meals_days")]
])

finish_selection_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("➡️ Продолжить", callback_data="choose_meals_days")]
])

# Префикс и извлечение названия продукта
product_prefix = "prod_"

def get_product_name(data: str) -> str | None:
    if data.startswith(product_prefix):
        return data[len(product_prefix):]
    return None
