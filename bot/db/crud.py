from __future__ import annotations
import json
from typing import Any, Dict, Optional, List
from sqlalchemy import select, desc
from .database import SessionLocal
from .models import Plan

async def save_plan(
    *,
    user_id: int,
    plan_md: str,
    requested_days: int,
    meals_per_day: int,
    feasible_days: int | None,
    decision: str | None,
    ingredients: list[dict] | None,
) -> str:
    async with SessionLocal() as session:
        rec = Plan(
            user_id=user_id,
            plan_md=plan_md,
            requested_days=requested_days,
            meals_per_day=meals_per_day,
            feasible_days=feasible_days,
            decision=decision,
            ingredients_json=json.dumps(ingredients or [], ensure_ascii=False),
        )
        session.add(rec)
        await session.commit()
        return rec.id

async def get_latest_plan(user_id: int) -> Optional[Dict[str, Any]]:
    async with SessionLocal() as session:
        q = select(Plan).where(Plan.user_id == user_id).order_by(desc(Plan.created_at)).limit(1)
        row = (await session.execute(q)).scalars().first()
        if not row:
            return None
        return {
            "id": row.id,
            "plan_md": row.plan_md,
            "requested_days": row.requested_days,
            "meals_per_day": row.meals_per_day,
            "feasible_days": row.feasible_days,
            "decision": row.decision,
            "ingredients": json.loads(row.ingredients_json or "[]"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

async def list_plan_summaries(user_id: int) -> List[Dict[str, Any]]:
    async with SessionLocal() as session:
        q = select(Plan).where(Plan.user_id == user_id).order_by(desc(Plan.created_at))
        rows = (await session.execute(q)).scalars().all()
        out: List[Dict[str, Any]] = []
        for r in rows:
            title = f"{r.requested_days}д × {r.meals_per_day}пп"
            if r.feasible_days is not None and r.feasible_days != r.requested_days:
                title += f" (посил.: {r.feasible_days}д)"
            out.append({"id": r.id, "title": title, "created_at": r.created_at.isoformat() if r.created_at else None})
        return out

async def get_plan_by_id(user_id: int, plan_id: str) -> Optional[Dict[str, Any]]:
    async with SessionLocal() as session:
        q = select(Plan).where(Plan.user_id == user_id, Plan.id == plan_id).limit(1)
        r = (await session.execute(q)).scalars().first()
        if not r:
            return None
        return {
            "id": r.id,
            "plan_md": r.plan_md,
            "requested_days": r.requested_days,
            "meals_per_day": r.meals_per_day,
            "feasible_days": r.feasible_days,
            "decision": r.decision,
            "ingredients": json.loads(r.ingredients_json or "[]"),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
