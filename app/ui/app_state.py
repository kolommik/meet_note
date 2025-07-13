"""
Модуль для управления состоянием приложения.
Содержит функции для инициализации, обновления и получения состояния из st.session_state.
"""

import streamlit as st
from utils.llm_stats import initialize_llm_stats


def initialize_app_state():
    """Инициализация состояния приложения"""
    # Базовые состояния
    if "file_status" not in st.session_state:
        st.session_state.file_status = "not_uploaded"
    if "file_path" not in st.session_state:
        st.session_state.file_path = None
    if "file_size" not in st.session_state:
        st.session_state.file_size = None

    # Состояния для транскрипции
    if "transcript_text" not in st.session_state:
        st.session_state.transcript_text = None

    # Состояния для анализа
    if "speaker_stats" not in st.session_state:
        st.session_state.speaker_stats = None
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "speaker_updated_transcript" not in st.session_state:
        st.session_state.speaker_updated_transcript = None

    # Состояния для исправлений
    if "correction_results" not in st.session_state:
        st.session_state.correction_results = None
    if "corrected_transcript" not in st.session_state:
        st.session_state.corrected_transcript = None

    # Состояния для документов
    if "transcript_document" not in st.session_state:
        st.session_state.transcript_document = None
    if "transcript_document_path" not in st.session_state:
        st.session_state.transcript_document_path = None
    if "meeting_summary" not in st.session_state:
        st.session_state.meeting_summary = None
    if "meeting_summary_path" not in st.session_state:
        st.session_state.meeting_summary_path = None

    # Инициализируем статистику LLM
    initialize_llm_stats()


def update_state(key, value):
    """
    Обновление состояния приложения

    Args:
        key: Ключ в session_state
        value: Новое значение
    """
    st.session_state[key] = value


def get_state(key, default=None):
    """
    Получение значения из состояния приложения

    Args:
        key: Ключ в session_state
        default: Значение по умолчанию, если ключ не найден

    Returns:
        Значение из session_state или default
    """
    return st.session_state.get(key, default)


def clear_state():
    """Очистка всего состояния приложения"""
    keys_to_clear = [
        "file_status",
        "file_path",
        "file_size",
        "transcript_text",
        "speaker_stats",
        "analysis_results",
        "speaker_updated_transcript",
        "correction_results",
        "corrected_transcript",
        "transcript_document",
        "transcript_document_path",
        "meeting_summary",
        "meeting_summary_path",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Возвращаем к начальному состоянию
    st.session_state.file_status = "not_uploaded"
