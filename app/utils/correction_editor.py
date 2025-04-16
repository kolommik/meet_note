"""
Модуль для редактирования исправлений ошибок распознавания в транскрипции.
Содержит функции для отображения интерфейса редактирования и
обновления транскрипции с учетом исправлений.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from utils.error_handler import safe_operation, ErrorType
from utils.logger import log_info


def display_correction_editor(
    correction_results: Dict[str, Any], transcript_text: str
) -> Optional[str]:
    """
    Отображает интерфейс для редактирования предложенных исправлений
    и применения изменений к транскрипции.

    Args:
        correction_results: Результаты анализа ошибок распознавания
        transcript_text: Текст транскрипции с именами спикеров

    Returns:
        Optional[str]: Обновленная транскрипция с исправлениями или None
    """
    return safe_operation(
        _display_correction_editor_impl,
        ErrorType.UNKNOWN_ERROR,
        correction_results=correction_results,
        transcript_text=transcript_text,
        default_return=None,
    )


def _display_correction_editor_impl(
    correction_results: Dict[str, Any], transcript_text: str
) -> Optional[str]:
    """Внутренняя реализация отображения редактора исправлений."""

    st.subheader("Редактирование исправлений ошибок распознавания")

    # Информация о функционале
    st.info(
        """
    В этом разделе вы можете просмотреть и отредактировать исправления ошибок распознавания, предложенные LLM.
    Выберите исправления, которые вы хотите применить, и при необходимости отредактируйте их.
    После редактирования нажмите «Применить исправления» для обновления транскрипции.
    """
    )

    # Проверяем наличие исправлений
    corrections = correction_results.get("corrections", [])
    if not corrections:
        st.warning("LLM не обнаружил ошибок распознавания в тексте.")
        return None

    # Инициализируем состояние для хранения пользовательских исправлений если его нет
    if "selected_corrections" not in st.session_state:
        st.session_state.selected_corrections = {
            correction["original"]: True for correction in corrections
        }

    if "edited_corrections" not in st.session_state:
        st.session_state.edited_corrections = {
            correction["original"]: correction["corrected"]
            for correction in corrections
        }

    # Отображаем заголовок со статистикой исправлений
    st.markdown(f"#### Найдено {len(corrections)} потенциальных ошибок распознавания")

    # Создаем форму для редактирования исправлений
    with st.form("correction_edit_form"):
        # Заголовки столбцов
        col1, col2, col3, col4 = st.columns([0.1, 0.35, 0.35, 0.2])
        with col1:
            st.markdown("**Выбор**")
        with col2:
            st.markdown("**Оригинал**")
        with col3:
            st.markdown("**Исправление**")
        with col4:
            st.markdown("**Уверенность**")

        # Отделяющая линия
        st.markdown("---")

        # Отображаем каждое исправление в виде строки
        for idx, correction in enumerate(corrections):
            original_text = correction["original"]
            corrected_text = correction["corrected"]
            confidence = correction.get("confidence", 0.0)
            explanation = correction.get("explanation", "")

            col1, col2, col3, col4 = st.columns([0.1, 0.35, 0.35, 0.2])

            # Колонка с чекбоксом для выбора
            with col1:
                selected = st.checkbox(
                    "",
                    value=st.session_state.selected_corrections.get(
                        original_text, True
                    ),
                    key=f"select_{idx}",
                )
                st.session_state.selected_corrections[original_text] = selected

            # Колонка с оригинальным текстом
            with col2:
                st.text_area(
                    "",
                    value=original_text,
                    key=f"original_{idx}",
                    disabled=True,
                    height=80,
                )

            # Колонка с исправленным текстом (редактируемым)
            with col3:
                edited_text = st.text_area(
                    "",
                    value=st.session_state.edited_corrections.get(
                        original_text, corrected_text
                    ),
                    key=f"corrected_{idx}",
                    height=80,
                )
                st.session_state.edited_corrections[original_text] = edited_text

            # Колонка с уверенностью и объяснением
            with col4:
                confidence_pct = int(confidence * 100)
                confidence_color = (
                    "green"
                    if confidence >= 0.8
                    else "orange" if confidence >= 0.5 else "red"
                )
                st.markdown(
                    f"<p style='color:{confidence_color};'><b>{confidence_pct}%</b></p>",
                    unsafe_allow_html=True,
                )
                if explanation:
                    with st.expander("Пояснение"):
                        st.markdown(f"_{explanation}_")

            # Отделяющая линия между исправлениями
            if idx < len(corrections) - 1:
                st.markdown("---")

        # Кнопка для применения исправлений
        submit_button = st.form_submit_button("Применить исправления к транскрипции")

    # Если кнопка нажата, обновляем транскрипцию
    if submit_button:
        log_info("Применение исправлений ошибок распознавания к транскрипции")

        # Создаем список выбранных исправлений
        selected_corrections = []
        for correction in corrections:
            original_text = correction["original"]

            # Проверяем, выбрано ли это исправление
            if st.session_state.selected_corrections.get(original_text, False):
                # Получаем отредактированный текст исправления
                edited_text = st.session_state.edited_corrections.get(
                    original_text, correction["corrected"]
                )

                # Создаем новый словарь с исправлением
                selected_corrections.append(
                    {"original": original_text, "corrected": edited_text}
                )

        # Обновляем транскрипцию
        corrected_transcript = update_transcript_with_corrections(
            transcript_text, selected_corrections
        )

        # Отображаем сообщение об успешном применении
        st.success(f"Применено {len(selected_corrections)} исправлений")

        return corrected_transcript

    return None


def update_transcript_with_corrections(
    transcript_text: str, corrections: List[Dict[str, str]]
) -> str:
    """
    Обновляет текст транскрипции, заменяя найденные ошибки на исправления.

    Args:
        transcript_text: Исходный текст транскрипции
        corrections: Список словарей с исправлениями
            (каждое исправление содержит ключи 'original' и 'corrected')

    Returns:
        str: Обновленная транскрипция с примененными исправлениями
    """
    return safe_operation(
        _update_transcript_with_corrections_impl,
        ErrorType.UNKNOWN_ERROR,
        transcript_text=transcript_text,
        corrections=corrections,
        default_return=transcript_text,
    )


def _update_transcript_with_corrections_impl(
    transcript_text: str, corrections: List[Dict[str, str]]
) -> str:
    """Внутренняя реализация обновления транскрипции с исправлениями."""

    corrected_text = transcript_text

    # Сортируем исправления по длине оригинала (от длинного к короткому)
    # для избежания проблем с частичной заменой
    sorted_corrections = sorted(
        corrections, key=lambda c: len(c["original"]), reverse=True
    )

    # Применяем каждое исправление последовательно
    for correction in sorted_corrections:
        original = correction["original"]
        corrected = correction["corrected"]

        # Проверяем, что оригинальный текст присутствует в транскрипции
        if original in corrected_text:
            # Заменяем все вхождения оригинального текста на исправленный
            corrected_text = corrected_text.replace(original, corrected)
            log_info(f"Заменено: '{original}' -> '{corrected}'")

    return corrected_text
