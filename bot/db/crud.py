from sqlalchemy import select
from db.database import SessionLocal
from db.models import MealPlan

# --- CREATE ---
async def create_meal_plan(user_id: str, products: list[str], days: int, meals: int, plan_text: str):
    """Создание нового плана питания"""
    async with SessionLocal() as session:
        plan = MealPlan(
            user_id=user_id,
            products=", ".join(products),
            days=days,
            meals_per_day=meals,
            plan_text=plan_text
        )
        session.add(plan)
        await session.commit()
        return plan


# --- READ ---
async def get_meal_plan(user_id: str):
    """Получение сохранённого плана пользователя"""
    async with SessionLocal() as session:
        result = await session.execute(
            select(MealPlan).where(MealPlan.user_id == user_id)
        )
        return result.scalars().first()


# --- UPDATE ---
async def update_meal_plan(user_id: str, new_text: str):
    """Обновление текста сохранённого плана"""
    async with SessionLocal() as session:
        result = await session.execute(
            select(MealPlan).where(MealPlan.user_id == user_id)
        )
        plan = result.scalars().first()
        if plan:
            plan.plan_text = new_text
            await session.commit()
        return plan


# --- DELETE ---
async def delete_meal_plan(user_id: str):
    """Удаление плана питания"""
    async with SessionLocal() as session:
        result = await session.execute(
            select(MealPlan).where(MealPlan.user_id == user_id)
        )
        plan = result.scalars().first()
        if plan:
            await session.delete(plan)
            await session.commit()
        return True
