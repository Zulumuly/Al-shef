# logic/gigachat.py
from __future__ import annotations

import os
import re
import json
import base64
import asyncio
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_gigachat import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()


# --- auth helpers -------------------------------------------------------------

def _normalize_auth_env() -> str:
    """
    Возвращает чистую base64-строку (Authorization data) для GigaChat.
    Допускает, что в .env могли случайно положить 'Basic ...' — префикс срежем.
    Валидируем, что это base64(client_id:client_secret).
    """
    raw = (os.getenv("GIGACHAT_AUTH") or "").strip()
    if not raw:
        raise RuntimeError(
            "GIGACHAT_AUTH пуст. Нужна base64-строка «Authorization data» из кабинета GigaChat "
            "(НЕ client secret и без префикса 'Basic ')."
        )
    if raw.lower().startswith("basic "):
        raw = raw[6:].strip()

    try:
        decoded = base64.b64decode(raw, validate=True).decode("utf-8")
    except Exception:
        raise RuntimeError("GIGACHAT_AUTH не является корректной base64-строкой.")
    if ":" not in decoded:
        raise RuntimeError(
            "Декодированный GIGACHAT_AUTH не выглядит как 'client_id:client_secret'."
        )
    return raw


_AUTH_B64 = _normalize_auth_env()

_gigachat = GigaChat(
    credentials=_AUTH_B64,
    scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
    model=os.getenv("GIGACHAT_MODEL", "GigaChat-Pro"),
    verify_ssl_certs=False,   # включи True, если у тебя корректные CA
    profanity_check=False,
)


# --- prompt helpers -----------------------------------------------------------

def _ingredients_to_text(ingredients: List[Dict]) -> str:
    if not ingredients:
        return "—"
    lines = []
    for it in ingredients:
        prod = str(it.get("product", "")).strip()
        grams = it.get("grams")
        lines.append(f"- {prod}" + (f" — {grams} г" if grams is not None else ""))
    return "\n".join(lines)


def _json_prompt(ingredients: List[Dict], days: int, meals_per_day: int) -> str:
    return (
        "Ты — профессиональный нутрициолог. "
        "Сначала оцени, хватит ли указанных продуктов на заявленные дни и приёмы пищи, "
        "потом сформируй план питания. Верни ОТВЕТ СТРОГО В JSON без пояснительного текста.\n\n"
        f"Доступные продукты:\n{_ingredients_to_text(ingredients)}\n\n"
        f"Запрошено дней: {days}\n"
        f"Приёмов пищи в день: {meals_per_day}\n\n"
        "Схема JSON ответа:\n"
        "{\n"
        '  "requested_days": <int>,\n'
        '  "meals_per_day": <int>,\n'
        '  "feasible_days_without_purchases": <int>,\n'
        '  "decision": "ok" | "reduce" | "need_purchases",\n'
        '  "summary_reason": "<кратко почему>",\n'
        '  "shortages": [ {"product":"...", "approx_grams_needed": <int>} ],\n'
        '  "shopping_list_for_requested_days": [ {"product":"...", "grams": <int>} ],\n'
        '  "plan_markdown": "<план в Markdown на feasible_days_without_purchases дней>"\n'
        "}\n\n"
        "- Если всего хватает на все дни → decision = \"ok\" и верни план на requested_days.\n"
        "- Если не хватает, но можно покрыть меньше дней без докупок → decision = \"reduce\" и верни "
        "  feasible_days_without_purchases < requested_days + план на это число дней.\n"
        "- Если без покупок сделать план нельзя (0 дней) → decision = \"need_purchases\" и верни shopping_list.\n"
        "- В plan_markdown для каждого дня укажи Завтрак/Обед/Ужин, порции (г) и примерную калорийность."
    )


def _extract_json_block(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


# --- public API ---------------------------------------------------------------

async def assess_and_plan(
    ingredients: List[Dict],
    days: int,
    meals_per_day: int
) -> Dict[str, Any]:
    """
    Просит модель вернуть JSON с оценкой достаточности и готовым планом.
    Возвращает dict с ключами:
      requested_days, meals_per_day, feasible_days_without_purchases, decision,
      summary_reason, shortages, shopping_list_for_requested_days, plan_markdown.
    В случае проблем — делает фоллбек и возвращает "decision": "fallback".
    """
    system = "Отвечай строго по инструкции. Если просят JSON — не добавляй ничего кроме JSON."
    human = _json_prompt(ingredients, days, meals_per_day)

    def _invoke_sync() -> str:
        res = _gigachat.invoke([SystemMessage(system), HumanMessage(human)])
        return getattr(res, "content", str(res))

    raw = await asyncio.to_thread(_invoke_sync)
    data = _extract_json_block(raw) or {}

    # валидируем минимум полей
    req_days = data.get("requested_days")
    feasible = data.get("feasible_days_without_purchases")
    decision = data.get("decision")

    if isinstance(req_days, int) and isinstance(feasible, int) and decision in {"ok", "reduce", "need_purchases"}:
        data.setdefault("requested_days", days)
        data.setdefault("meals_per_day", meals_per_day)
        return data

    # фоллбек: обычный текстовый план + подсказка про достаточность
    fb_human = (
        f"Составь подробный план питания на {days} дней, {meals_per_day} приёмов пищи в день.\n"
        f"Доступные продукты:\n{_ingredients_to_text(ingredients)}\n"
        "Если продуктов не хватает — предложи оптимальное число дней без докупок и список покупок для изначального запроса."
    )

    def _invoke_fb() -> str:
        res = _gigachat.invoke([SystemMessage("Нутрициолог, пиши на русском."), HumanMessage(fb_human)])
        return getattr(res, "content", str(res))

    fb_text = await asyncio.to_thread(_invoke_fb)
    return {
        "requested_days": days,
        "meals_per_day": meals_per_day,
        "feasible_days_without_purchases": days,  # не знаем — поставим = requested
        "decision": "fallback",
        "summary_reason": "Не удалось распарсить JSON, возвращён фоллбек-текст.",
        "shortages": [],
        "shopping_list_for_requested_days": [],
        "plan_markdown": fb_text,
    }


# Обратная совместимость: если где-то ещё вызывается старое API
async def generate_meal_plan(ingredients: List[Dict], days: int, meals_per_day: int) -> str:
    """
    Совместимая обёртка. Возвращает только текст плана.
    Внутри пользуется assess_and_plan.
    """
    res = await assess_and_plan(ingredients, days, meals_per_day)
    return (res.get("plan_markdown") or "").strip() or "Не удалось получить план."
