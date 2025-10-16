from db.database import async_session_maker
from db.models import MealPlan


async def create_meal_plan(user_id, products, days, meals_per_day, plan_text):
    try:
        user_id = int(user_id) if user_id is not None else 0
        days = int(days) if days else 0
        meals_per_day = int(meals_per_day) if meals_per_day else 0

        async with async_session_maker() as session:
            new_plan = MealPlan(
                user_id=user_id,
                products=str(products),
                days=days,
                meals_per_day=meals_per_day,
                plan_text=str(plan_text),
            )
            session.add(new_plan)
            await session.commit()
            print(f"Meal plan saved for user {user_id}")

    except ValueError as ve:
        print(f"Ошибка преобразования типов: {ve}")
    except Exception as e:
        print(f"Ошибка при сохранении плана: {e}")


async def get_meal_plan(user_id):
    try:
        user_id = int(user_id)
        async with async_session_maker() as session:
            result = await session.execute(
                """
                SELECT plan_text
                FROM meal_plans
                WHERE user_id = :user_id
                ORDER BY id DESC
                LIMIT 1
                """,
                {"user_id": user_id},
            )
            row = result.first()
            if row:
                print(f"Найден сохранённый план питания для пользователя {user_id}")
                return row[0]
            print(f"ℹУ пользователя {user_id} нет сохранённых планов")
            return None
    except ValueError as ve:
        print(f"Ошибка преобразования ID пользователя: {ve}")
        return None
    except Exception as e:
        print(f"Ошибка при получении плана: {e}")
        return None
