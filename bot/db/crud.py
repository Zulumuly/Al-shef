# bot/db/crud.py
from sqlalchemy import select, desc
from .database import AsyncSessionLocal
from .models import Plan, Recipe

# --- Работа с планами ---------------------------------------------------------

async def save_plan(title: str, content: str):
    async with AsyncSessionLocal() as session:
        plan = Plan(title=title, content=content)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        return plan

async def get_latest_plan():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Plan).order_by(desc(Plan.id)).limit(1)
        )
        return result.scalar_one_or_none()

async def list_plan_summaries():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Plan.id, Plan.title))
        return result.all()

async def get_plan_by_id(plan_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        return result.scalar_one_or_none()

# --- Работа с рецептами -------------------------------------------------------

async def save_recipe(name: str, ingredients: str, instructions: str):
    async with AsyncSessionLocal() as session:
        recipe = Recipe(name=name, ingredients=ingredients, instructions=instructions)
        session.add(recipe)
        await session.commit()
        await session.refresh(recipe)
        return recipe

async def list_recipes():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Recipe.id, Recipe.name))
        return result.all()

async def get_recipe_by_id(recipe_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        return result.scalar_one_or_none()
