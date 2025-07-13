"""
Модуль для управления компонентами исправления ошибок распознавания.
Содержит функции для отображения элементов управления исправлениями
и отображения результатов исправлений.
"""

import streamlit as st
import os
from utils.error_handler import safe_operation, ErrorType
from utils.logger import log_info
from utils.transcript_correction import identify_corrections_with_llm
from utils.correction_editor import display_correction_editor
from utils.llm_stats import update_llm_stats
from ui.app_state import get_state, update_state
from utils.speech_to_text import get_transcript_file_path
from ui.ui_components import copy_button


def render_correction_controls():
    """Отрисовка компонента для исправления ошибок распознавания"""
    st.subheader("Исправление ошибок распознавания")

    # Получаем текст с обработанными спикерами
    transcript_text = get_state("speaker_updated_transcript")
    if not transcript_text:
        st.warning("Текст с определенными спикерами не найден")
        return

    # Используем настройки LLM из сайдбара, если они установлены
    llm_settings = get_state("llm_settings", {})
    model_name = llm_settings.get("model")
    llm_strategy = llm_settings.get("strategy")

    # Получаем конфигурацию из session_state
    config = st.session_state.config

    # Путь к контекстному файлу
    context_file = os.path.join(config.context_dir, "terms.md")

    context_text = ""
    if os.path.exists(context_file):
        try:
            with open(context_file, "r", encoding="utf-8") as file:
                context_text = file.read()
            st.success("Загружен контекстный файл: terms.md")
        except Exception as e:
            st.warning(f"Не удалось загрузить контекстный файл: {str(e)}")
    else:
        st.info(
            f"Контекстный файл не найден. Создайте файл {config.context_dir}/terms.md \
                для улучшения распознавания специфических терминов."
        )

    if llm_strategy:
        # Кнопка для запуска анализа исправлений с помощью LLM
        if st.button("Найти ошибки распознавания с помощью LLM"):
            with st.spinner("Анализ ошибок распознавания с помощью LLM..."):
                # Используем safe_operation для обработки ошибок
                correction_results = safe_operation(
                    _identify_corrections_with_llm,
                    ErrorType.LLM_ERROR,
                    operation_name="Анализ ошибок распознавания",
                    show_ui_error=True,
                    transcript_text=transcript_text,
                    context_text=context_text,
                    llm_strategy=llm_strategy,
                    model_name=model_name,
                )

                # Сохраняем результаты анализа исправлений
                if correction_results:
                    update_state("correction_results", correction_results)

        # Отображаем результаты анализа исправлений, если они есть
        correction_results = get_state("correction_results")
        if correction_results:
            st.subheader("Предлагаемые исправления")

            # Отображаем редактор исправлений
            corrected_transcript = display_correction_editor(
                correction_results, transcript_text
            )

            # Если транскрипция была исправлена, сохраняем её
            if corrected_transcript:
                log_info("Транскрипция исправлена на основе предложений LLM")

                # Определяем путь для сохранения исправленной транскрипции
                file_path = get_state("file_path")
                corrected_transcript_path = get_transcript_file_path(file_path).replace(
                    ".txt", "_corrected.txt"
                )

                # Сохраняем исправленную транскрипцию
                with open(corrected_transcript_path, "w", encoding="utf-8") as file:
                    file.write(corrected_transcript)

                update_state("corrected_transcript", corrected_transcript)
                update_state("file_status", "corrections_processed")

                # Обновляем страницу для отображения изменений
                st.rerun()
    else:
        st.info(
            "Для анализа ошибок распознавания укажите настройки LLM в боковой панели или выберите модель выше"
        )


def render_correction_content():
    """Показываем результаты с исправлениями ошибок распознавания"""
    if st.toggle("Исправленная транскрипция", value=False, key="correction_toggle"):
        corrected_text = get_state("corrected_transcript")

        if corrected_text:
            st.subheader("Итоговая транскрипция")

            # Отображаем текст
            st.text_area(
                "Исправленная транскрипция",
                corrected_text,
                height=250,
                key="corrected_text_area",
            )

            copy_button(corrected_text)


def _identify_corrections_with_llm(
    transcript_text, context_text, llm_strategy, model_name
):
    """Анализ ошибок распознавания с помощью LLM"""
    # Получаем настройки LLM из session_state или используем значения по умолчанию
    llm_settings = get_state("llm_settings", {})
    temperature = llm_settings.get("temperature")
    max_tokens = llm_settings.get("max_tokens")

    # Запускаем анализ с помощью LLM с параметрами из настроек
    correction_results = identify_corrections_with_llm(
        transcript_text=transcript_text,
        context_text=context_text,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Обновляем статистику LLM и получаем текущие метрики
    llm_stats = update_llm_stats(llm_strategy, model_name)

    # Сохраняем статистику текущего запроса
    update_state("llm_stats", llm_stats)

    return correction_results
