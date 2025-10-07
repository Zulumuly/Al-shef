# logic/gigachat.py
from __future__ import annotations

import os
import re
import json
import base64
import asyncio
import logging
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_gigachat import GigaChat
from langchain.schema import SystemMessage, HumanMessage  # ✅ новый импорт

load_dotenv()

logger = logging.getLogger(__name__)

# --- auth helpers -------------------------------------------------------------

def _normalize_auth_env() -> str:
    """Возвращает чистую base64-строку (Authorization data) для GigaChat."""
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
        if ":" not in decoded:
            raise ValueError("Отсутствует разделитель ':'")
    except Exception as e:
        raise RuntimeError(f"GIGACHAT_AUTH не является корректной base64-строкой: {e}")
    return raw

_AUTH_B64 = _normalize_auth_env()

# --- client init --------------------------------------------------------------

try:
    _gigachat = GigaChat(
        credentials=_AUTH_B64,
        scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
        model=os.getenv("GIGACHAT_MODEL", "GigaChat-Pro"),
        verify_ssl_certs=False,
        profanity_check=False,
        timeout=30,
    )
    logger.info("✅ GigaChat клиент успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка инициализации GigaChat: {e}")
    raise

# --- helpers ------------------------------------------------------------------

def _ingredients_to_text(ingredients: List[Dict]) -> str:
    if not ingredients:
        return "—"
    return "\n".join(
        f"- {it.get('product','')} — {it.get('grams')} г"
        if it.get("grams") else f"- {it.get('product','')} (количество не указано)"
        for it in ingredients if it.get("product")
    )

def _json_prompt(ingredients: List[Dict], days: int, meals_per_day: int) -> str:
    ingredients_text = _ingredients_to_text(ingredients)
    return (
        "Ты — кулинарный ассистент и нутрициолог. "
        "Составь план питания, используя ТОЛЬКО продукты из списка. "
        "Верни ответ строго в JSON.\n\n"
        f"ДОСТУПНЫЕ ПРОДУКТЫ:\n{ingredients_text}\n\n"
        f"ЗАПРОШЕНО: {days} дней × {meals_per_day} приёмов пищи\n\n"
        "JSON СХЕМА ОТВЕТА:\n"
        "{\n"
        '  "requested_days": ..., \n'
        '  "meals_per_day": ..., \n'
        '  "feasible_days_without_purchases": ..., \n'
        '  "decision": "ok|reduce|need_purchases", \n'
        '  "plan_markdown": "## План рецептов..."\n'
        "}"
    )

def _extract_json_block(text: str) -> dict | None:
    patterns = [r"```json\n(.*?)\n```", r"```\n(.*?)\n```", r"\{.*\}"]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    try:
        start, end = text.find("{"), text.rfind("}") + 1
        return json.loads(text[start:end]) if start >= 0 else None
    except Exception:
        return None

# --- main API -----------------------------------------------------------------

async def assess_and_plan(ingredients: List[Dict], days: int, meals_per_day: int) -> Dict[str, Any]:
    logger.info(f"Запрос плана: {days}д × {meals_per_day}п, {len(ingredients)} продуктов")
    if days <= 0 or meals_per_day <= 0:
        raise ValueError("Дни и приёмы пищи должны быть > 0")

    if not ingredients:
        return {
            "requested_days": days,
            "meals_per_day": meals_per_day,
            "feasible_days_without_purchases": 0,
            "decision": "need_purchases",
            "plan_markdown": "## ❌ Не указаны продукты\nДобавьте продукты для создания плана."
        }

    prompt = _json_prompt(ingredients, days, meals_per_day)

    try:
        def _invoke_sync() -> str:
            response = _gigachat.invoke([SystemMessage(content="Ты ассистент."), HumanMessage(content=prompt)])
            return getattr(response, "content", str(response))

        raw_response = await asyncio.to_thread(_invoke_sync)
        data = _extract_json_block(raw_response)

        if data and "plan_markdown" in data:
            return data
        else:
            logger.warning("Не удалось извлечь JSON. Фоллбек.")
    except Exception as e:
        logger.error(f"Ошибка в GigaChat: {e}")

    return await _generate_fallback_plan(ingredients, days, meals_per_day)

async def _generate_fallback_plan(ingredients: List[Dict], days: int, meals_per_day: int) -> Dict[str, Any]:
    text = f"План питания на {days} дней × {meals_per_day} приёмов:\n{_ingredients_to_text(ingredients)}"
    return {
        "requested_days": days,
        "meals_per_day": meals_per_day,
        "feasible_days_without_purchases": days,
        "decision": "fallback",
        "plan_markdown": text,
    }

async def generate_meal_plan(ingredients: List[Dict], days: int, meals_per_day: int) -> str:
    res = await assess_and_plan(ingredients, days, meals_per_day)
    return res.get("plan_markdown", "Не удалось получить план.")
