"""
Модуль для анализа спикеров в транскрипциях.
Содержит функции для подсчета статистики спикеров
и идентификации их имен и ролей с помощью LLM.
"""

import re
from typing import Dict, Any
import json
from utils.prompts import PROMPTS
from utils.error_handler import safe_operation, ErrorType


def calculate_speaker_statistics(transcript_text: str) -> Dict[str, Dict[str, Any]]:
    """
    Подсчитывает статистику для каждого спикера в транскрипции.

    Args:
        transcript_text: Текст транскрипции в формате 'speaker_X: текст'

    Returns:
        Dict: Словарь со статистикой по каждому спикеру и общими данными
    """
    return safe_operation(
        _calculate_speaker_statistics_impl,
        ErrorType.TRANSCRIPTION_ERROR,
        transcript_text=transcript_text,
        default_return={},
    )


def _calculate_speaker_statistics_impl(
    transcript_text: str,
) -> Dict[str, Dict[str, Any]]:
    """Внутренняя реализация расчета статистики спикеров."""
    # Регулярное выражение для поиска паттернов "speaker_X: текст"
    pattern = r"(speaker_\d+):\s+(.*?)(?=\n(?:speaker_\d+):|$)"

    # Поиск всех совпадений
    matches = re.findall(pattern, transcript_text, re.DOTALL)

    # Словарь для хранения данных по каждому спикеру
    speaker_stats = {}
    total_words = 0

    # Обрабатываем каждое совпадение
    for speaker, text in matches:
        # Подсчитываем слова в высказывании (разделяем по пробелам)
        words = text.strip().split()
        word_count = len(words)
        total_words += word_count

        # Если спикер уже есть в словаре, обновляем его статистику
        if speaker in speaker_stats:
            speaker_stats[speaker]["word_count"] += word_count
            speaker_stats[speaker]["utterances"] += 1
        else:
            # Иначе создаем новую запись
            speaker_stats[speaker] = {"word_count": word_count, "utterances": 1}

    # Рассчитываем процент для каждого спикера
    for speaker in speaker_stats:
        speaker_stats[speaker]["percentage"] = round(
            (speaker_stats[speaker]["word_count"] / total_words) * 100, 2
        )

    # Добавляем общую статистику
    speaker_stats["total"] = {
        "word_count": total_words,
        "utterances": sum(
            s["utterances"]
            for s in speaker_stats.values()
            if s != speaker_stats.get("total", None)
        ),
        "speakers_count": len(speaker_stats),
    }

    return speaker_stats


def identify_speakers_with_llm(
    transcript_text: str,
    speaker_stats: Dict[str, Dict[str, Any]],
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> Dict[str, Any]:
    """
    Использует LLM для определения имен спикеров и анализа разговора.

    Args:
        transcript_text: Текст транскрипции
        speaker_stats: Статистика по спикерам (из calculate_speaker_statistics)
        llm_strategy: Стратегия для взаимодействия с LLM
        model_name: Название модели для использования
        temperature: Температура генерации (случайность)
        max_tokens: Максимальное количество токенов в ответе

    Returns:
        Dict: Результаты анализа LLM
    """
    return safe_operation(
        _identify_speakers_with_llm_impl,
        ErrorType.LLM_ERROR,
        transcript_text=transcript_text,
        speaker_stats=speaker_stats,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        default_return={
            "error": "Ошибка при анализе с помощью LLM",
            "speakers": {},
            "summary": "Не удалось получить результаты анализа",
        },
    )


def _identify_speakers_with_llm_impl(
    transcript_text: str,
    speaker_stats: Dict[str, Dict[str, Any]],
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> Dict[str, Any]:
    """Внутренняя реализация анализа спикеров с помощью LLM."""
    # Подготовка статистики для включения в промпт
    stats_text = ""
    for speaker, data in speaker_stats.items():
        if speaker != "total":
            stats_text += f"{speaker}: {data['word_count']} слов, {data['percentage']}% от общего объема\n"

    # Составляем системный промпт из шаблона
    system_prompt = PROMPTS["transcript_analysis_system"].format()

    # Составляем сообщение пользователя из шаблона
    user_message = PROMPTS["transcript_analysis_user"].format(
        stats_text=stats_text, transcript_text=transcript_text
    )

    # Отправляем запрос к LLM с указанными параметрами
    response, _ = llm_strategy.send_message(
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
        analysis_results = json.loads(json_str)

        # Объединяем результаты со статистикой
        for speaker, data in analysis_results.get("speakers", {}).items():
            if speaker in speaker_stats and speaker != "total":
                # Добавляем статистику к результатам анализа
                data["statistics"] = {
                    "word_count": speaker_stats[speaker]["word_count"],
                    "percentage": speaker_stats[speaker]["percentage"],
                    "utterances": speaker_stats[speaker]["utterances"],
                }

        return analysis_results

    except json.JSONDecodeError:
        # Если не удалось распарсить JSON, возвращаем сырой ответ
        return {
            "error": "Не удалось распарсить ответ в формате JSON",
            "raw_response": response,
        }
