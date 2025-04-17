"""
Модуль для управления компонентами анализа спикеров.
Содержит функции для отображения элементов управления анализом спикеров
и отображения результатов анализа.
"""

import streamlit as st
from utils.error_handler import safe_operation, ErrorType
from utils.logger import log_info
from utils.speaker_analysis import (
    calculate_speaker_statistics,
    identify_speakers_with_llm,
)
from utils.speaker_editor import display_speaker_editor
from utils.speech_to_text import get_transcript_file_path
from utils.llm_stats import update_llm_stats
from ui.app_state import get_state, update_state
from ui.ui_components import copy_button


def render_speaker_define_controls():
    """Отрисовка компонента анализа спикеров"""
    st.subheader("Анализ спикеров")

    # Получаем текст
    transcript_text = get_state("transcript_text")
    if not transcript_text:
        st.warning("Текст спикеров не найден")
        return

    # Получаем статистику спикеров или вычисляем её
    speaker_stats = get_state("speaker_stats")
    if not speaker_stats:
        with st.spinner("Подсчет статистики спикеров..."):
            speaker_stats = calculate_speaker_statistics(transcript_text)
            update_state("speaker_stats", speaker_stats)

    # Анилизируем спикеров с помощью LLM
    # Используем настройки из сайдбара, если они установлены
    llm_settings = get_state("llm_settings", {})
    model_name = llm_settings.get("model")
    llm_strategy = llm_settings.get("strategy")

    if llm_strategy:
        # Кнопка для запуска анализа с помощью LLM
        if st.button("Провести анализ с помощью LLM"):
            with st.spinner("Анализ разговора с помощью LLM..."):
                # Используем safe_operation для обработки ошибок
                analysis_results = safe_operation(
                    _define_speakers_with_llm,
                    ErrorType.LLM_ERROR,
                    operation_name="Анализ с помощью LLM",
                    show_ui_error=True,
                    transcript_text=transcript_text,
                    speaker_stats=speaker_stats,
                    llm_strategy=llm_strategy,
                    model_name=model_name,
                )

                # Сохраняем результаты анализа
                if analysis_results:
                    update_state("analysis_results", analysis_results)

        # Отображаем результаты анализа, если они есть
        analysis_results = get_state("analysis_results")
        if analysis_results:
            st.subheader("Результаты анализа транскрипции")

            # Добавляем общее описание
            if "summary" in analysis_results:
                st.markdown(f"#### Тема разговора\n{analysis_results['summary']}\n")

            # Добавляем редактор имен спикеров
            updated_transcript = display_speaker_editor(
                analysis_results, transcript_text
            )

            # Если транскрипция была обновлена, сохраняем её
            if updated_transcript:
                log_info("Транскрипция обновлена с именами спикеров")

                # Определяем путь для сохранения обновленной транскрипции
                file_path = get_state("file_path")
                updated_transcript_path = get_transcript_file_path(file_path).replace(
                    ".txt", "_named.txt"
                )

                # Сохраняем обновленную транскрипцию
                with open(updated_transcript_path, "w", encoding="utf-8") as file:
                    file.write(updated_transcript)

                update_state("speaker_updated_transcript", updated_transcript)
                update_state("file_status", "speakers_processed")

                # Обновляем страницу для отображения изменений
                st.rerun()
    else:
        st.info(
            "Для анализа транскрипции укажите настройки LLM в боковой панели или выберите модель выше"
        )


def render_speaker_define_content():
    """Показываем результаты с исправлениями имен спикеров"""
    speaker_updated_text = get_state("speaker_updated_transcript")
    if speaker_updated_text:
        if st.toggle(
            "Транскрипция с именами спикеров", value=False, key="speaker_define_toggle"
        ):
            st.subheader("Обновленная транскрипция")
            # Отображаем текст
            st.text_area(
                "Транскрипция с именами спикеров",
                speaker_updated_text,
                height=250,
                key="speaker_define_text_area",
            )
            copy_button(speaker_updated_text)


def _define_speakers_with_llm(transcript_text, speaker_stats, llm_strategy, model_name):
    """Анализ транскрипции с помощью LLM"""
    # Получаем настройки LLM из session_state или используем значения по умолчанию
    llm_settings = get_state("llm_settings", {})
    temperature = llm_settings.get("temperature", 0.0)
    max_tokens = llm_settings.get("max_tokens", 2048)

    # Запускаем анализ с помощью LLM с параметрами из настроек
    analysis_results = identify_speakers_with_llm(
        transcript_text=transcript_text,
        speaker_stats=speaker_stats,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Обновляем статистику LLM и получаем текущие метрики
    llm_stats = update_llm_stats(llm_strategy, model_name)

    # Сохраняем статистику текущего запроса
    update_state("llm_stats", llm_stats)

    return analysis_results
