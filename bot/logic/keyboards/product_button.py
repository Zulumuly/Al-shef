from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Главное меню выбора категории продуктов
category_menu = InlineKeyboardMarkup([
    [InlineKeyboardButton("🥦 Овощи", callback_data="cat_vegetables"),
     InlineKeyboardButton("🍎 Фрукты", callback_data="cat_fruits")],
    [InlineKeyboardButton("🍖 Мясо", callback_data="cat_meat"),
     InlineKeyboardButton("🍞 Бакалея", callback_data="cat_grocery")],
    [InlineKeyboardButton("🧀 Молочное", callback_data="cat_dairy"),
     InlineKeyboardButton("🌾 Зерновое", callback_data="cat_grains")],
    [InlineKeyboardButton("✅ Завершить выбор", callback_data="finish_selection")]
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
     InlineKeyboardButton("🥔 Кабачок", callback_data="prod_Кабачок")],
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

# Бакалея
grocery_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍚 Рис", callback_data="add_Рис"),
     InlineKeyboardButton("🫘 Фасоль", callback_data="add_Фасоль")],
    [InlineKeyboardButton("🧂 Соль", callback_data="add_Соль")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

# Молочное
dairy_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🥛 Молоко", callback_data="add_Молоко"),
     InlineKeyboardButton("🧀 Сыр", callback_data="add_Сыр")],
    [InlineKeyboardButton("🍦 Йогурт", callback_data="add_Йогурт")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

# Зерновое
grains_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍞 Хлеб", callback_data="add_Хлеб"),
     InlineKeyboardButton("🥣 Овсянка", callback_data="add_Овсянка")],
    [InlineKeyboardButton("🌽 Кукуруза", callback_data="add_Кукуруза")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])


product_keyboards = {
    "cat_vegetables": vegetables_keyboard,
    "cat_fruits": fruits_keyboard,
}