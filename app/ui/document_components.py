"""
Модуль содержит компоненты UI для отображения и работы с документами по встрече.
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path
from utils.file_handler import save_markdown_document
from utils.llm_stats import update_llm_stats
from ui.app_state import get_state, update_state
from ui.ui_components import copy_button
from utils.document_generation import generate_meeting_summary


def render_document_controls():
    """
    Рендерит элементы управления для генерации документов по встрече
    """
    st.header("📝 Документы по встрече")

    # Объясняем, что будет создано
    st.info(
        "На этом шаге можно создать два документа по встрече:\n"
        "1. **Документ транскрипта встречи** - содержит краткое содержание, "
        "список участников и полный транскрипт.\n"
        "2. **Саммари встречи** - содержит ключевые темы, согласованные действия и открытые вопросы."
    )

    # Получаем необходимые данные из состояния
    llm_settings = get_state("llm_settings", {})
    model_name = llm_settings.get("model")
    llm_strategy = llm_settings.get("strategy")
    temperature = llm_settings.get("temperature", 0.0)
    max_tokens = llm_settings.get("max_tokens", 2048)

    transcript_text = get_state("corrected_transcript") or get_state(
        "speaker_updated_transcript"
    )
    analysis_results = get_state("analysis_results", {})

    # Проверяем наличие необходимых данных
    if not transcript_text or not analysis_results:
        st.warning(
            "Нет данных для создания документов. Пожалуйста, выполните предыдущие шаги."
        )
        return

    if not llm_strategy:
        st.error(
            "Не удалось получить стратегию LLM. Пожалуйста, проверьте настройки LLM в боковой панели."
        )
        return

    # Кнопка для генерации документов
    documents_exist = get_state("transcript_document") and get_state("meeting_summary")
    button_text = "Обновить документы" if documents_exist else "Создать документы"

    if st.button(button_text, type="primary"):

        with st.spinner("Генерация документов..."):
            # Генерируем документы
            try:
                summary_doc = generate_meeting_summary(
                    transcript_text=transcript_text,
                    analysis_results=analysis_results,
                    llm_strategy=llm_strategy,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                transcript_doc = transcript_text

                # Сохраняем документы в файлы
                file_base_name = Path(get_state("file_path", "meeting")).stem
                transcript_doc_path = save_markdown_document(
                    content=transcript_doc, filename=f"{file_base_name}_transcript.md"
                )
                summary_doc_path = save_markdown_document(
                    content=summary_doc, filename=f"{file_base_name}_summary.md"
                )

                # Обновляем состояние
                update_state("transcript_document", transcript_doc)
                update_state("transcript_document_path", transcript_doc_path)
                update_state("meeting_summary", summary_doc)
                update_state("meeting_summary_path", summary_doc_path)
                update_state("file_status", "documents_created")

                # Обновляем статистику LLM
                llm_stats = update_llm_stats(llm_strategy, model_name)
                update_state("llm_stats", llm_stats)

                st.success("Документы успешно созданы!")
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка при создании документов: {str(e)}")


def render_document_content():
    """
    Рендерит содержимое документов по встрече
    """
    if get_state("file_status") != "documents_created":
        return

    st.header("📝 Документы по встрече")

    # Получаем данные документов
    transcript_doc = get_state("transcript_document", "")
    summary_doc = get_state("meeting_summary", "")
    transcript_doc_path = get_state("transcript_document_path", "")
    summary_doc_path = get_state("meeting_summary_path", "")

    # Получаем базовое имя исходного файла для использования при скачивании
    file_base_name = Path(get_state("file_path", "meeting")).stem

    # Создаем вкладки для отображения документов
    doc_tab1, doc_tab2 = st.tabs(["Транскрипт встречи", "Саммари встречи"])

    with doc_tab1:
        st.markdown(transcript_doc)
        col1, col2, _ = st.columns([1, 1, 1])
        with col1:
            if transcript_doc_path:
                create_download_button(
                    transcript_doc, f"{file_base_name}_transcript.md"
                )
        with col2:
            copy_button(transcript_doc)

    with doc_tab2:
        st.markdown(summary_doc)
        col1, col2, _ = st.columns([1, 1, 1])
        with col1:
            if summary_doc_path:
                create_download_button(summary_doc, f"{file_base_name}_summary.md")
        with col2:
            copy_button(summary_doc)


def create_download_button(content, filename, button_text="💾 Скачать документ"):
    """
    Создает кнопку для скачивания содержимого как файла.

    Args:
        content: Содержимое файла
        filename: Имя файла для скачивания
        button_text: Текст кнопки
    """
    # Кодируем содержимое в base64
    b64 = base64.b64encode(content.encode()).decode()

    # Создаем HTML для скачивания с одинаковым стилем
    html_code = f"""
    <div>
        <a href="data:file/txt;base64,{b64}" download="{filename}" style="text-decoration:none;">
            <button style="
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
                border-radius: 0.3rem;
                width: 100%;">
                {button_text}
            </button>
        </a>
    </div>
    """

    # Отображаем HTML
    components.html(html_code, height=60)
