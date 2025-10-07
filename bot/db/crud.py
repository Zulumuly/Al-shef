# db/crud.py
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .models import NutritionPlan, SavedRecipe
from .database import get_session

logger = logging.getLogger(__name__)


# --- Nutrition Plans ----------------------------------------------------------

async def save_plan(
    user_id: int,
    plan_md: str,
    requested_days: int,
    meals_per_day: int,
    feasible_days: int | None = None,
    decision: str | None = None,
    ingredients: list[dict] | None = None,
) -> str:
    """Сохраняет план питания в БД и возвращает его ID."""
    async for session in get_session():
        title = f"План на {feasible_days or requested_days} дней"
        plan = NutritionPlan(
            user_id=user_id,
            title=title,
            plan_md=plan_md,
            requested_days=requested_days,
            meals_per_day=meals_per_day,
            feasible_days=feasible_days,
            decision=decision,
            ingredients=ingredients or []
        )
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        return str(plan.id)


async def get_latest_plan(user_id: int) -> dict | None:
    """Возвращает последний сохранённый план пользователя."""
    async for session in get_session():
        stmt = (
            select(NutritionPlan)
            .where(NutritionPlan.user_id == user_id)
            .order_by(desc(NutritionPlan.created_at))
            .limit(1)
        )
        plan = (await session.execute(stmt)).scalar_one_or_none()
        if not plan:
            return None
        return plan.__dict__


async def list_plan_summaries(user_id: int, limit: int = 10) -> list[dict]:
    """Возвращает список последних планов пользователя."""
    async for session in get_session():
        stmt = (
            select(NutritionPlan)
            .where(NutritionPlan.user_id == user_id)
            .order_by(desc(NutritionPlan.created_at))
            .limit(limit)
        )
        plans = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(p.id),
                "title": p.title,
                "created_at": p.created_at,
                "requested_days": p.requested_days,
                "feasible_days": p.feasible_days,
            }
            for p in plans
        ]


async def get_plan_by_id(user_id: int, plan_id: str) -> dict | None:
    """Возвращает план по ID."""
    async for session in get_session():
        stmt = (
            select(NutritionPlan)
            .where(NutritionPlan.user_id == user_id, NutritionPlan.id == plan_id)
        )
        plan = (await session.execute(stmt)).scalar_one_or_none()
        return plan.__dict__ if plan else None


# --- Saved Recipes ------------------------------------------------------------

async def save_recipe(
    user_id: int,
    title: str,
    recipe_md: str,
    ingredients: list[dict] | None = None,
    plan_id: str | None = None,
) -> str:
    """Сохраняет рецепт в отдельной таблице."""
    async for session in get_session():
        recipe = SavedRecipe(
            user_id=user_id,
            plan_id=plan_id,
            title=title,
            recipe_md=recipe_md,
            ingredients=ingredients or []
        )
        session.add(recipe)
        await session.commit()
        await session.refresh(recipe)
        return str(recipe.id)


async def list_recipes(user_id: int, limit: int = 10) -> list[dict]:
    """Возвращает список сохранённых рецептов пользователя."""
    async for session in get_session():
        stmt = (
            select(SavedRecipe)
            .where(SavedRecipe.user_id == user_id)
            .order_by(desc(SavedRecipe.created_at))
            .limit(limit)
        )
        recipes = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(r.id),
                "title": r.title,
                "created_at": r.created_at,
                "ingredients": r.ingredients,
            }
            for r in recipes
        ]


async def get_recipe_by_id(user_id: int, recipe_id: str) -> dict | None:
    """Возвращает рецепт по ID."""
    async for session in get_session():
        stmt = (
            select(SavedRecipe)
            .where(SavedRecipe.user_id == user_id, SavedRecipe.id == recipe_id)
        )
        recipe = (await session.execute(stmt)).scalar_one_or_none()
        return recipe.__dict__ if recipe else None
