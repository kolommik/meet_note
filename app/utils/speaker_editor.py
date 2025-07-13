"""
Модуль для редактирования информации о спикерах в транскрипции.
Содержит функции для отображения интерфейса редактирования и
обновления транскрипции с учетом имен спикеров.
"""

import streamlit as st
import re
from typing import Dict, Any, List, Optional
from utils.error_handler import safe_operation, ErrorType
from utils.logger import log_info

SPEAKER_PARTICIPATION_LIMIT = 15
SPEAKER_PARTICIPATION_CUTOFF = 5


def extract_speaker_examples(
    transcript_text: str, speaker_id: str, max_examples: int = 3
) -> List[str]:
    """
    Извлекает примеры высказываний спикера из транскрипции

    Args:
        transcript_text: Текст транскрипции
        speaker_id: ID спикера для поиска
        max_examples: Максимальное количество примеров

    Returns:
        List[str]: Список примеров высказываний
    """
    return safe_operation(
        _extract_speaker_examples_impl,
        ErrorType.UNKNOWN_ERROR,
        transcript_text=transcript_text,
        speaker_id=speaker_id,
        max_examples=max_examples,
        default_return=[],
    )


def _extract_speaker_examples_impl(
    transcript_text: str, speaker_id: str, max_examples: int = 3
) -> List[str]:
    """Внутренняя реализация извлечения примеров высказываний спикера."""

    # Регулярное выражение для поиска высказываний спикера
    pattern = rf"{speaker_id}:\s+(.*?)(?=\n(?:speaker_\d+):|$)"

    # Находим все высказывания спикера
    matches = re.findall(pattern, transcript_text, re.DOTALL)

    # Отбираем только не пустые высказывания
    statements = [s.strip() for s in matches if s.strip()]

    # Отсортируем по длине, чтобы выбрать наиболее содержательные примеры
    statements.sort(key=len, reverse=True)

    # Выбираем примеры для отображения (предпочитаем более длинные)
    examples = []

    # Сначала берем длинные фразы (больше 50 символов)
    long_statements = [s for s in statements if len(s) > 50]
    if long_statements:
        examples.extend(long_statements[: max_examples // 2])

    # Затем добавляем средние фразы для разнообразия
    remaining = max_examples - len(examples)
    if remaining > 0:
        medium_statements = [
            s for s in statements if 20 < len(s) <= 50 and s not in examples
        ]
        examples.extend(medium_statements[:remaining])

    # Если все еще не хватает примеров, добавляем короткие фразы
    remaining = max_examples - len(examples)
    if remaining > 0:
        short_statements = [s for s in statements if len(s) <= 20 and s not in examples]
        examples.extend(short_statements[:remaining])

    # Если примеров меньше, чем max_examples, берем первые из оставшихся
    remaining = max_examples - len(examples)
    if remaining > 0 and len(statements) > len(examples):
        remaining_statements = [s for s in statements if s not in examples]
        examples.extend(remaining_statements[:remaining])

    # Ограничиваем длину каждого примера для отображения
    truncated_examples = []
    for example in examples:
        if len(example) > 100:
            truncated = example[:97] + "..."
        else:
            truncated = example
        truncated_examples.append(truncated)

    return truncated_examples[:max_examples]


def display_speaker_editor(
    analysis_results: Dict[str, Any], transcript_text: str
) -> Optional[str]:
    """
    Отображает интерфейс для редактирования имен спикеров
    и применения изменений к транскрипции

    Args:
        analysis_results: Результаты анализа с именами спикеров
        transcript_text: Текст транскрипции

    Returns:
        Optional[str]: Обновленная транскрипция с именами или None
    """
    return safe_operation(
        _display_speaker_editor_impl,
        ErrorType.UNKNOWN_ERROR,
        analysis_results=analysis_results,
        transcript_text=transcript_text,
        default_return=None,
    )


def _display_speaker_editor_impl(
    analysis_results: Dict[str, Any], transcript_text: str
) -> Optional[str]:
    """Внутренняя реализация отображения редактора спикеров."""

    st.subheader("Редактирование имен спикеров")

    # Информация о функционале
    st.info(
        """
    В этом разделе вы можете отредактировать имена спикеров, определенные LLM.
    Спикеры отсортированы по их вкладу в беседу (% участия).
    После редактирования нажмите «Применить изменения» для обновления транскрипции.
    """
    )

    # Инициализируем состояние для хранения пользовательских имен если его нет
    if "user_speaker_names" not in st.session_state:
        st.session_state.user_speaker_names = {}

    # Создаем список спикеров и сортируем по % участия (убывание)
    speakers_data = []
    for speaker_id, speaker_info in analysis_results.get("speakers", {}).items():
        if "statistics" in speaker_info:
            speaker_name = speaker_info.get("name", speaker_id)
            if speaker_name == "Неизвестно":
                speaker_name = speaker_id
            percentage = speaker_info["statistics"].get("percentage", 0)
            speakers_data.append(
                {
                    "id": speaker_id,
                    "percentage": percentage,
                    "llm_name": speaker_name,
                    "role": speaker_info.get("role", "Не определена"),
                    "confidence": speaker_info.get("confidence", "низкая"),
                    "word_count": speaker_info["statistics"].get("word_count", 0),
                    "utterances": speaker_info["statistics"].get("utterances", 0),
                }
            )

    # Сортируем по проценту участия
    speakers_data.sort(key=lambda x: x["percentage"], reverse=True)

    with st.form("speaker_edit_form"):
        # Отображаем каждого спикера как expander
        for speaker in speakers_data:
            # Определяем цвет заголовка в зависимости от участия
            header_style = ""
            if speaker["percentage"] > SPEAKER_PARTICIPATION_LIMIT:
                header_style = "background-color: rgba(76, 175, 80, 0.2); padding: 10px; border-radius: 5px;"
            elif speaker["percentage"] > SPEAKER_PARTICIPATION_CUTOFF:
                header_style = "background-color: rgba(33, 150, 243, 0.1); padding: 10px; border-radius: 5px;"

            # Создаем контейнер с соответствующим стилем
            with st.container():
                st.markdown(f"<div style='{header_style}'>", unsafe_allow_html=True)

                # Создаем expander для каждого спикера
                with st.expander(
                    f"{speaker['id']} [{speaker['llm_name']}]: {speaker['percentage']}% \
                        участия ({speaker['word_count']} слов, {speaker['utterances']} высказываний)",
                    expanded=(speaker["percentage"] > SPEAKER_PARTICIPATION_LIMIT),
                ):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.write(f"**Предполагаемое имя:** {speaker['llm_name']}")
                        st.write(f"**Роль в беседе:** {speaker['role']}")
                        st.write(f"**Уверенность LLM:** {speaker['confidence']}")

                    with col2:
                        # Позволяем пользователю редактировать имя
                        # Используем предыдущее значение если оно есть, иначе предложенное LLM
                        default_name = st.session_state.user_speaker_names.get(
                            speaker["id"], speaker["llm_name"]
                        )

                        new_name = st.text_input(
                            "Имя спикера",
                            value=default_name,
                            key=f"name_{speaker['id']}",
                        )

                        # Сохраняем введенное пользователем имя
                        st.session_state.user_speaker_names[speaker["id"]] = new_name

                        # Чекбокс для игнорирования спикера
                        ignore_speaker = st.checkbox(
                            "Игнорировать этого спикера",
                            value=False,
                            key=f"ignore_{speaker['id']}",
                        )
                        if ignore_speaker:
                            st.session_state.user_speaker_names[speaker["id"]] = ""

                    # Добавляем примеры фраз спикера
                    examples = extract_speaker_examples(
                        transcript_text, speaker["id"], max_examples=3
                    )
                    if examples:
                        st.write("**Примеры высказываний:**")
                        for i, example in enumerate(examples, 1):
                            st.markdown(f"{i}. _{example}_")
                    else:
                        st.write("_Примеры высказываний не найдены_")

                # Закрываем div стиля
                st.markdown("</div>", unsafe_allow_html=True)

                # Добавляем небольшой отступ между спикерами
                st.write("")

        # Кнопка применения изменений
        submit_button = st.form_submit_button("Применить изменения к транскрипции")

    # Если кнопка нажата, обновляем транскрипцию
    if submit_button:
        log_info("Применение изменений имен спикеров к транскрипции")

        # Фильтруем спикеров по порогу
        filtered_names = {}
        for speaker in speakers_data:
            speaker_id = speaker["id"]
            if speaker["percentage"] < SPEAKER_PARTICIPATION_CUTOFF:
                # Игнорируем спикеров ниже порога
                continue

            # Для остальных спикеров берем пользовательские имена
            name = st.session_state.user_speaker_names.get(speaker_id, "")
            if name:  # Добавляем только если имя не пустое
                filtered_names[speaker_id] = name

        # Обновляем транскрипцию
        updated_transcript = update_transcript_with_names(
            transcript_text, filtered_names
        )

        return updated_transcript

    return None


def update_transcript_with_names(
    transcript_text: str, speaker_names: Dict[str, str]
) -> str:
    """
    Обновляет текст транскрипции, заменяя ID спикеров на их имена

    Args:
        transcript_text: Исходный текст транскрипции
        speaker_names: Словарь сопоставления ID спикеров и имен

    Returns:
        str: Обновленная транскрипция с именами вместо ID
    """
    return safe_operation(
        _update_transcript_with_names_impl,
        ErrorType.UNKNOWN_ERROR,
        transcript_text=transcript_text,
        speaker_names=speaker_names,
        default_return=transcript_text,
    )


def _update_transcript_with_names_impl(
    transcript_text: str, speaker_names: Dict[str, str]
) -> str:
    """Внутренняя реализация обновления транскрипции с именами спикеров."""

    lines = transcript_text.split("\n")
    updated_lines = []

    for line in lines:
        updated_line = line

        # Ищем ID спикера в начале строки (pattern: "speaker_X: ")
        for speaker_id, name in speaker_names.items():
            if line.startswith(f"{speaker_id}:"):
                # Заменяем ID на имя
                updated_line = line.replace(f"{speaker_id}:", f"{name}:")
                break

        updated_lines.append(updated_line)

    return "\n".join(updated_lines)
