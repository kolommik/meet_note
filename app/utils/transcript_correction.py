"""
Модуль для исправления ошибок распознавания в транскрипциях.
Содержит функции для анализа и исправления ошибок
в распознанном тексте с помощью LLM.
"""

import re
from typing import Dict, Any, Optional
import json
from utils.prompts import PROMPTS
from utils.error_handler import safe_operation, ErrorType


def identify_corrections_with_llm(
    transcript_text: str,
    context_text: Optional[str],
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """
    Использует LLM для поиска и исправления ошибок распознавания в транскрипции.

    Args:
        transcript_text: Текст транскрипции с именами спикеров
        context_text: Дополнительный контекст для улучшения распознавания (может быть None)
        llm_strategy: Стратегия для взаимодействия с LLM
        model_name: Название модели для использования
        temperature: Температура генерации (случайность)
        max_tokens: Максимальное количество токенов в ответе

    Returns:
        Dict: Результаты анализа ошибок распознавания
    """
    return safe_operation(
        _identify_corrections_with_llm_impl,
        ErrorType.LLM_ERROR,
        transcript_text=transcript_text,
        context_text=context_text,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        default_return={
            "error": "Ошибка при анализе ошибок распознавания с помощью LLM",
            "corrections": [],
        },
    )


def _identify_corrections_with_llm_impl(
    transcript_text: str,
    context_text: Optional[str],
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """Внутренняя реализация анализа ошибок распознавания с помощью LLM."""
    # Проверяем наличие контекста и устанавливаем значение по умолчанию
    if context_text is None:
        context_text = "Контекстная информация отсутствует."

    # Составляем системный промпт из шаблона
    system_prompt = PROMPTS["transcript_correction_system"].format()

    # Составляем сообщение пользователя из шаблона
    user_message = PROMPTS["transcript_correction_user"].format(
        context_text=context_text, transcript_text=transcript_text
    )

    # Отправляем запрос к LLM с указанными параметрами
    response = llm_strategy.send_message(
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        model_name=model_name,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # Пытаемся распарсить JSON из ответа
    try:
        # Ищем JSON в ответе
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            # Если JSON не обернут в код, пробуем использовать весь ответ
            json_str = response

        # Пытаемся распарсить JSON
        correction_results = json.loads(json_str)

        # Проверяем наличие ключа corrections в ответе
        if "corrections" not in correction_results:
            correction_results["corrections"] = []

        return correction_results

    except json.JSONDecodeError:
        # Если не удалось распарсить JSON, возвращаем сырой ответ
        return {
            "parsing_error": True,
            "raw_response": response,
            "corrections": [],
        }
