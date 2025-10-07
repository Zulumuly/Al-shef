# logic/gigachat.py
from __future__ import annotations

import os
import re
import json
import base64
import asyncio
from typing import List, Dict, Any
import logging

from dotenv import load_dotenv
from langchain_gigachat import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

logger = logging.getLogger(__name__)

# --- auth helpers -------------------------------------------------------------

def _normalize_auth_env() -> str:
    """
    Возвращает чистую base64-строку (Authorization data) для GigaChat.
    Очищает переносы строк и лишний префикс "Basic ".
    """
    raw = (os.getenv("GIGACHAT_AUTH") or "").strip().replace("\n", "")
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
            raise ValueError("Отсутствует разделитель ':' в декодированных данных")
    except Exception as e:
        raise RuntimeError(f"GIGACHAT_AUTH не является корректной base64-строкой: {e}")

    return raw


_AUTH_B64 = _normalize_auth_env()

# --- GigaChat client ----------------------------------------------------------

try:
    _gigachat = GigaChat(
        credentials=_AUTH_B64,
        scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
        model=os.getenv("GIGACHAT_MODEL", "GigaChat-Pro"),
        verify_ssl_certs=False,
        profanity_check=False,
        timeout=60,  # увеличил для Render
    )
    logger.info("GigaChat клиент успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка инициализации GigaChat: {e}")
    raise


# --- helpers -----------------------------------------------------------------

def _ingredients_to_text(ingredients: List[Dict]) -> str:
    if not ingredients:
        return "—"
    lines = []
    for it in ingredients:
        prod = str(it.get("product") or "").strip()
        grams = it.get("grams")
        if not prod:
            continue
        if isinstance(grams, (int, float)) and grams > 0:
            lines.append(f"- {prod} — {int(grams)} г")
        else:
            lines.append(f"- {prod} (количество не указано)")
    return "\n".join(lines)


def _json_prompt(ingredients: List[Dict], days: int, meals_per_day: int) -> str:
    ingredients_text = _ingredients_to_text(ingredients)
    return (
        "Ты — кулинарный ассистент и нутрициолог. "
        "Твоя задача: СОСТАВИТЬ ПЛАН ПИТАНИЯ на заданные дни и приёмы пищи, "
        "используя ТОЛЬКО перечисленные пользователем ингредиенты "
        "(и базовые специи: соль, перец, вода, растительное масло, сушёные травы). "
        "Суммарный расход каждого продукта по всему плану НЕ должен превышать доступное количество.\n\n"

        "ВАЖНЫЕ ТРЕБОВАНИЯ:\n"
        "• На КАЖДЫЙ день и КАЖДЫЙ приём укажи ОДИН конкретный рецепт с названием\n"
        "• Для каждого рецепта явно перечисли ингредиенты с граммами ИЗ КОРЗИНЫ\n"
        "• Дай пошаговые инструкции (1, 2, 3…), время готовки и количество порций\n"
        "• Не повторяй одно и то же блюдо чаще, чем через один приём пищи\n"
        "• В конце плана добавь «Сводный расход» по каждому продукту\n"
        "• Если продуктов не хватает — сократи число дней до посильного и объясни почему\n"
        "• ВЕРНИ ОТВЕТ СТРОГО В JSON ФОРМАТЕ (без текста вне JSON)\n\n"

        f"ДОСТУПНЫЕ ПРОДУКТЫ:\n{ingredients_text}\n\n"
        f"ЗАПРОШЕНО: {days} дней × {meals_per_day} приёмов пищи\n\n"

        "JSON СХЕМА ОТВЕТА:\n"
        "{\n"
        f'  "requested_days": {days},\n'
        f'  "meals_per_day": {meals_per_day},\n'
        '  "feasible_days_without_purchases": 3,\n'
        '  "decision": "ok",\n'
        '  "summary_reason": "Продуктов хватает на весь период",\n'
        '  "shortages": [],\n'
        '  "shopping_list_for_requested_days": [],\n'
        '  "plan_markdown": "## План рецептов..."\n'
        "}\n"
    )


def _extract_json_block(text: str) -> dict | None:
    """Извлекает JSON из текста ответа."""
    if not text:
        return None

    text = text.strip()
    if text.lower().startswith("ответ:"):
        text = text.split(":", 1)[1].strip()

    patterns = [
        r"```json\n(.*?)\n```",
        r"```\n(.*?)\n```",
        r"\{.*\}"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass

    return None


def _validate_response(data: dict) -> bool:
    required_fields = [
        "requested_days", "meals_per_day", "feasible_days_without_purchases",
        "decision", "plan_markdown"
    ]
    if not all(field in data for field in required_fields):
        return False
    if not isinstance(data["feasible_days_without_purchases"], int):
        return False
    if data["decision"] not in {"ok", "reduce", "need_purchases"}:
        return False
    if not isinstance(data["plan_markdown"], str) or not data["plan_markdown"]:
        return False
    return True


# --- public API ---------------------------------------------------------------

async def assess_and_plan(
    ingredients: List[Dict],
    days: int,
    meals_per_day: int
) -> Dict[str, Any]:
    logger.info(f"Запрос плана: {days}д × {meals_per_day}п, {len(ingredients)} продуктов")

    if days <= 0 or meals_per_day <= 0:
        raise ValueError("Дни и приемы пищи должны быть положительными числами")

    if not ingredients:
        return {
            "requested_days": days,
            "meals_per_day": meals_per_day,
            "feasible_days_without_purchases": 0,
            "decision": "need_purchases",
            "summary_reason": "Не указаны продукты",
            "shortages": [],
            "shopping_list_for_requested_days": [],
            "plan_markdown": "## ❌ Не указаны продукты\nДобавьте продукты для создания плана питания."
        }

    system_msg = "Ты — кулинарный ассистент. Отвечай строго в JSON формате."
    human_msg = _json_prompt(ingredients, days, meals_per_day)

    try:
        def _invoke_sync() -> str:
            response = _gigachat.invoke([
                SystemMessage(system_msg),
                HumanMessage(human_msg)
            ])
            return getattr(response, "content", str(response))

        raw_response = await asyncio.to_thread(_invoke_sync)
        data = _extract_json_block(raw_response)

        if data and _validate_response(data):
            return data
    except Exception as e:
        logger.error(f"Ошибка при обращении к GigaChat: {e}")

    return await _generate_fallback_plan(ingredients, days, meals_per_day)


async def _generate_fallback_plan(
    ingredients: List[Dict],
    days: int,
    meals_per_day: int
) -> Dict[str, Any]:
    fallback_prompt = (
        f"Составь план питания на {days} дней, {meals_per_day} приёмов пищи в день.\n"
        f"Доступные продукты:\n{_ingredients_to_text(ingredients)}\n"
    )
    try:
        def _invoke_fallback() -> str:
            response = _gigachat.invoke([
                SystemMessage("Ты — кулинарный ассистент. Пиши на русском."),
                HumanMessage(fallback_prompt)
            ])
            return getattr(response, "content", str(response))

        fallback_text = await asyncio.to_thread(_invoke_fallback)
        return {
            "requested_days": days,
            "meals_per_day": meals_per_day,
            "feasible_days_without_purchases": days,
            "decision": "fallback",
            "summary_reason": "Использован упрощенный план",
            "shortages": [],
            "shopping_list_for_requested_days": [],
            "plan_markdown": "## Упрощённый план\n" + fallback_text,
        }
    except Exception as e:
        logger.error(f"Ошибка в фоллбеке: {e}")
        return _get_error_response(days, meals_per_day)


def _get_error_response(days: int, meals_per_day: int) -> Dict[str, Any]:
    return {
        "requested_days": days,
        "meals_per_day": meals_per_day,
        "feasible_days_without_purchases": 0,
        "decision": "error",
        "summary_reason": "Техническая ошибка",
        "shortages": [],
        "shopping_list_for_requested_days": [],
        "plan_markdown": "## ⚠️ Сервис временно недоступен",
    }


async def generate_meal_plan(ingredients: List[Dict], days: int, meals_per_day: int) -> str:
    res = await assess_and_plan(ingredients, days, meals_per_day)
    return (res.get("plan_markdown") or "").strip() or "Не удалось получить план."
