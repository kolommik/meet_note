"""
Модуль для генерации саммари документов на основе транскрипций с помощью LLM.
"""

from typing import Dict, Any
from utils.prompts import PROMPTS
from utils.error_handler import safe_operation, ErrorType
from utils.llm_stats import update_llm_stats


def generate_meeting_summary(
    transcript_text: str,
    analysis_results: Dict[str, Any],
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> str:
    """
    Генерирует документ с саммари встречи с использованием LLM.

    Args:
        transcript_text: Текст транскрипции
        analysis_results: Результаты анализа спикеров
        llm_strategy: Стратегия для взаимодействия с LLM
        model_name: Название модели для использования
        temperature: Температура генерации (случайность)
        max_tokens: Максимальное количество токенов в ответе

    Returns:
        str: Markdown-документ с саммари встречи
    """
    # Подготовка информации об участниках
    participants_info = ""
    for speaker, data in analysis_results.get("speakers", {}).items():
        name = data.get("name", "Неизвестно")
        role = data.get("role", "Роль не определена")
        participants_info += f"- {speaker} ({name}): {role}\n"
    if not participants_info:
        participants_info = "Информация об участниках отсутствует."

    # Подготовка системного промпта
    system_prompt = PROMPTS["meeting_summary_system"].format()

    # Подготовка пользовательского сообщения
    # Для саммари пока передаем весь текст, т.к. логика с чанками для саммари сложнее
    user_message = PROMPTS["meeting_summary_user"].format(
        participants_info=participants_info, transcript_text=transcript_text
    )

    summary_content, _ = safe_operation(
        llm_strategy.send_message,
        ErrorType.LLM_ERROR,
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        model_name=model_name,
        max_tokens=max_tokens,
        temperature=temperature,
        default_return="# Саммари встречи\n\n*Не удалось сгенерировать саммари из-за технической ошибки.*",
    )
    if (
        summary_content
        != "# Саммари встречи\n\n*Не удалось сгенерировать саммари из-за технической ошибки.*"
    ):
        update_llm_stats(llm_strategy, model_name)

    return summary_content
