"""
Модуль для генерации документов на основе транскрипций.
Содержит функции для создания транскрипта встречи,
саммари и других документов с помощью LLM.
"""

import re
from typing import Dict, Any, List, Tuple
from utils.prompts import PROMPTS
from utils.error_handler import safe_operation, ErrorType
from utils.llm_stats import update_llm_stats


def _split_transcript_for_processing(
    transcript_text: str, max_chunk_size: int = 4000
) -> List[str]:
    """
    Разделяет текст транскрипта на разумные части для обработки.

    Разделение происходит на границах высказываний, чтобы сохранить целостность реплик.

    Args:
        transcript_text: Полный текст транскрипта
        max_chunk_size: Максимальный размер одной части в символах

    Returns:
        List[str]: Список частей транскрипта
    """
    # Если текст короткий, возвращаем его целиком
    if len(transcript_text) <= max_chunk_size:
        return [transcript_text]

    # Регулярное выражение для поиска паттернов "speaker_X: текст"
    pattern = r"(speaker_\d+):\s+(.*?)(?=\n(?:speaker_\d+):|$)"

    # Поиск всех совпадений
    matches = re.findall(pattern, transcript_text, re.DOTALL)

    # Формируем части транскрипта
    chunks = []
    current_chunk = ""

    for speaker, text in matches:
        # Формируем текущую реплику
        utterance = f"{speaker}: {text}\n"

        # Если добавление этой реплики превысит максимальный размер части,
        # добавляем текущую часть в список и начинаем новую
        if len(current_chunk) + len(utterance) > max_chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = utterance
        else:
            current_chunk += utterance

    # Добавляем последнюю часть, если она не пуста
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def generate_large_document(
    system_prompt: str,
    initial_message: str,
    continuation_data: List[str],
    continuation_instruction: str,
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens_per_request: int = 2048,
    max_retries: int = 3,
) -> str:
    """
    Генерирует большой документ с использованием потоковой генерации через LLM.

    Метод разделяет входные данные на части и постепенно генерирует документ,
    используя предыдущие сгенерированные части как контекст для следующих.

    Args:
        system_prompt: Системный промпт с общими инструкциями
        initial_message: Начальное сообщение, содержащее инструкции и первую часть данных
        continuation_data: Список оставшихся частей данных для постепенной генерации
        continuation_instruction: Инструкция для продолжения генерации
        llm_strategy: Стратегия для взаимодействия с LLM
        model_name: Название модели для использования
        temperature: Температура генерации (случайность)
        max_tokens_per_request: Максимальное количество токенов на один запрос
        max_retries: Максимальное количество попыток в случае ошибки

    Returns:
        str: Полный сгенерированный документ
    """
    return safe_operation(
        _generate_large_document_impl,
        ErrorType.LLM_ERROR,
        system_prompt=system_prompt,
        initial_message=initial_message,
        continuation_data=continuation_data,
        continuation_instruction=continuation_instruction,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens_per_request=max_tokens_per_request,
        max_retries=max_retries,
        default_return="# Документ\n\n*Не удалось сгенерировать документ из-за технической ошибки.*",
    )


def _generate_large_document_impl(
    system_prompt: str,
    initial_message: str,
    continuation_data: List[str],
    continuation_instruction: str,
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens_per_request: int = 2048,
    max_retries: int = 3,
) -> str:
    """Внутренняя реализация генерации большого документа через потоковую генерацию."""
    # Генерируем начальную часть документа
    current_document = llm_strategy.send_message(
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": initial_message}],
        model_name=model_name,
        max_tokens=max_tokens_per_request,
        temperature=temperature,
    )

    # Обновляем статистику LLM после начального запроса
    update_llm_stats(llm_strategy, model_name)

    # Если данных для продолжения нет, возвращаем текущий документ
    if not continuation_data:
        return current_document

    # Последовательно обрабатываем оставшиеся части данных
    for data_chunk in continuation_data:
        retry_count = 0
        success = False

        while not success and retry_count < max_retries:
            try:
                # Создаем промпт для продолжения генерации
                continuation_message = f"{continuation_instruction}\n\n \
                    Предыдущая часть документа:\n{current_document[-2000:]}\n\n \
                    Дополнительные данные:\n{data_chunk}"

                # Генерируем продолжение документа
                continuation = llm_strategy.send_message(
                    system_prompt=system_prompt,
                    messages=[{"role": "user", "content": continuation_message}],
                    model_name=model_name,
                    max_tokens=max_tokens_per_request,
                    temperature=temperature,
                )

                # Обновляем статистику LLM после каждого запроса продолжения
                update_llm_stats(llm_strategy, model_name)

                # Добавляем продолжение к текущему документу
                current_document += "\n" + continuation
                success = True

            except Exception:
                retry_count += 1
                if retry_count >= max_retries:
                    # Если исчерпаны все попытки, добавляем уведомление об ошибке
                    current_document += "\n\n*Не удалось сгенерировать полный документ из-за технической ошибки.*"

    return current_document


def generate_transcript_document(
    transcript_text: str,
    analysis_results: Dict[str, Any],
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> str:
    """
    Генерирует документ транскрипта встречи с использованием LLM.

    Использует потоковую генерацию для создания документов любого размера.

    Args:
        transcript_text: Текст транскрипции
        analysis_results: Результаты анализа спикеров
        llm_strategy: Стратегия для взаимодействия с LLM
        model_name: Название модели для использования
        temperature: Температура генерации (случайность)
        max_tokens: Максимальное количество токенов в ответе

    Returns:
        str: Markdown-документ с транскриптом встречи
    """
    # Подготовка информации об участниках
    participants_info = ""
    for speaker, data in analysis_results.get("speakers", {}).items():
        name = data.get("name", "Неизвестно")
        role = data.get("role", "Роль не определена")
        participants_info += f"{speaker} - {name} ({role})\n"

    # Разделяем транскрипт на управляемые части для обработки
    transcript_chunks = _split_transcript_for_processing(transcript_text)

    # Подготовка системного промпта
    system_prompt = PROMPTS["transcript_document_system"].format()

    # Подготовка начального сообщения с инструкциями и первой частью транскрипта
    initial_chunk = transcript_chunks[0] if transcript_chunks else transcript_text
    initial_message = PROMPTS["transcript_document_user"].format(
        participants_info=participants_info, transcript_text=initial_chunk
    )

    # Остальные части транскрипта (если есть)
    continuation_data = transcript_chunks[1:] if len(transcript_chunks) > 1 else []

    # Инструкция для продолжения генерации
    continuation_instruction = """
    Продолжи генерацию документа на основе дополнительных данных транскрипции.
    Сохраняй структуру и форматирование документа, продолжай с того места, где закончился предыдущий фрагмент.
    """

    # Используем потоковую генерацию для создания документа
    return generate_large_document(
        system_prompt=system_prompt,
        initial_message=initial_message,
        continuation_data=continuation_data,
        continuation_instruction=continuation_instruction,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens_per_request=max_tokens,
    )


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

    Использует потоковую генерацию для создания документов любого размера.

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
        participants_info += f"{speaker} - {name} ({role})\n"

    # Разделяем транскрипт на управляемые части для обработки
    transcript_chunks = _split_transcript_for_processing(transcript_text)

    # Подготовка системного промпта
    system_prompt = PROMPTS["meeting_summary_system"].format()

    # Подготовка начального сообщения с инструкциями и первой частью транскрипта
    initial_chunk = transcript_chunks[0] if transcript_chunks else transcript_text
    initial_message = PROMPTS["meeting_summary_user"].format(
        participants_info=participants_info, transcript_text=initial_chunk
    )

    # Остальные части транскрипта (если есть)
    continuation_data = transcript_chunks[1:] if len(transcript_chunks) > 1 else []

    # Инструкция для продолжения генерации
    continuation_instruction = """
    Продолжи генерацию саммари на основе дополнительных данных транскрипции.
    Учитывай уже сгенерированную часть саммари и дополняй её новой информацией из предоставленных данных.
    Сохраняй структуру документа и не повторяй уже упомянутую информацию.
    """

    # Используем потоковую генерацию для создания документа
    return generate_large_document(
        system_prompt=system_prompt,
        initial_message=initial_message,
        continuation_data=continuation_data,
        continuation_instruction=continuation_instruction,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens_per_request=max_tokens,
    )


def generate_meeting_documents(
    transcript_text: str,
    analysis_results: Dict[str, Any],
    llm_strategy,
    model_name: str,
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> Tuple[str, str]:
    """
    Генерирует оба документа по встрече: транскрипт и саммари.

    Args:
        transcript_text: Текст транскрипции
        analysis_results: Результаты анализа спикеров
        llm_strategy: Стратегия для взаимодействия с LLM
        model_name: Название модели для использования
        temperature: Температура генерации (случайность)
        max_tokens: Максимальное количество токенов в ответе

    Returns:
        Tuple[str, str]: Tuple из двух Markdown-документов (транскрипт, саммари)
    """
    transcript_doc = generate_transcript_document(
        transcript_text=transcript_text,
        analysis_results=analysis_results,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    summary_doc = generate_meeting_summary(
        transcript_text=transcript_text,
        analysis_results=analysis_results,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return transcript_doc, summary_doc
