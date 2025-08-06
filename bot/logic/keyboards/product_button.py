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

# Овощи
vegetables_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🥕 Морковь", callback_data="add_Морковь"),
     InlineKeyboardButton("🥔 Картофель", callback_data="add_Картофель")],
    [InlineKeyboardButton("🍅 Помидоры", callback_data="add_Помидоры"),
     InlineKeyboardButton("🥒 Огурцы", callback_data="add_Огурцы")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

# Фрукты
fruits_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍏 Яблоко", callback_data="add_Яблоко"),
     InlineKeyboardButton("🍌 Банан", callback_data="add_Банан")],
    [InlineKeyboardButton("🍊 Апельсин", callback_data="add_Апельсин")],
    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")]
])

# Мясо
meat_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍗 Курица", callback_data="add_Курица"),
     InlineKeyboardButton("🥩 Говядина", callback_data="add_Говядина")],
    [InlineKeyboardButton("🥓 Свинина", callback_data="add_Свинина")],
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
    
}