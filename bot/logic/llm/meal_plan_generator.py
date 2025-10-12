from logic.llm.gigachat_api import ask_gigachat

def generate_meal_plan(products, days, meals_per_day):
    prompt = f"""
    У меня есть следующие продукты: {', '.join(products)}.
    Составь план питания на {days} дней, {meals_per_day} приёмов пищи в день.
    Если продуктов не хватает, предложи оптимальный вариант исходя из доступных ингредиентов.
    Верни структурированный план по дням.
    """
    return ask_gigachat(prompt)
