# db/crud.py
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging
from .models import NutritionPlan
from .session import get_db_session

logger = logging.getLogger(__name__)

async def save_plan(
    user_id: int,
    plan_md: str,
    requested_days: int,
    meals_per_day: int,
    feasible_days: int | None = None,
    decision: str | None = None,
    ingredients: list[dict] | None = None,
) -> str:
    """Сохраняет план питания в базу данных."""
    async with get_db_session() as session:
        try:
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
            
            logger.info(f"Plan saved for user {user_id}, plan_id: {plan.id}")
            return str(plan.id)
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving plan: {e}")
            raise

async def get_latest_plan(user_id: int) -> dict | None:
    """Возвращает последний сохраненный план пользователя."""
    async with get_db_session() as session:
        try:
            stmt = (
                select(NutritionPlan)
                .where(NutritionPlan.user_id == user_id)
                .order_by(desc(NutritionPlan.created_at))
                .limit(1)
            )
            
            result = await session.execute(stmt)
            plan = result.scalar_one_or_none()
            
            if plan:
                return {
                    "id": str(plan.id),
                    "title": plan.title,
                    "plan_md": plan.plan_md,
                    "requested_days": plan.requested_days,
                    "meals_per_day": plan.meals_per_day,
                    "feasible_days": plan.feasible_days,
                    "decision": plan.decision,
                    "ingredients": plan.ingredients,
                    "created_at": plan.created_at
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest plan: {e}")
            return None

async def list_plan_summaries(user_id: int, limit: int = 10) -> list[dict]:
    """Возвращает список планов пользователя."""
    async with get_db_session() as session:
        try:
            stmt = (
                select(NutritionPlan)
                .where(NutritionPlan.user_id == user_id)
                .order_by(desc(NutritionPlan.created_at))
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            plans = result.scalars().all()
            
            return [
                {
                    "id": str(plan.id),
                    "title": plan.title,
                    "created_at": plan.created_at,
                    "requested_days": plan.requested_days,
                    "feasible_days": plan.feasible_days
                }
                for plan in plans
            ]
            
        except Exception as e:
            logger.error(f"Error listing plans: {e}")
            return []

async def get_plan_by_id(user_id: int, plan_id: str) -> dict | None:
    """Возвращает план по ID."""
    async with get_db_session() as session:
        try:
            stmt = (
                select(NutritionPlan)
                .where(
                    NutritionPlan.user_id == user_id,
                    NutritionPlan.id == plan_id
                )
            )
            
            result = await session.execute(stmt)
            plan = result.scalar_one_or_none()
            
            if plan:
                return {
                    "id": str(plan.id),
                    "title": plan.title,
                    "plan_md": plan.plan_md,
                    "requested_days": plan.requested_days,
                    "meals_per_day": plan.meals_per_day,
                    "feasible_days": plan.feasible_days,
                    "decision": plan.decision,
                    "ingredients": plan.ingredients,
                    "created_at": plan.created_at
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting plan by ID: {e}")
            return None