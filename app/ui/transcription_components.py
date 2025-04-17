"""
Модуль для управления компонентами транскрипции интерфейса.
Содержит функции для отображения элементов управления транскрипцией
и отображения результатов транскрипции.
"""

import streamlit as st
import os
from utils.speech_to_text import (
    transcribe_audio,
    get_transcript_file_path,
    read_transcript,
)
from utils.error_handler import safe_operation, ErrorType
from ui.app_state import get_state, update_state
from ui.ui_components import copy_button


def render_transcription_controls():
    """Отрисовка элементов управления для транскрипции"""
    # Кнопка для распознавания речи
    if st.button("Распознать речь", key="transcribe_button"):
        file_path = get_state("file_path")

        if file_path:
            with st.spinner("Распознавание речи..."):
                # Используем safe_operation для обработки ошибок
                transcription_result = safe_operation(
                    transcribe_audio,
                    ErrorType.TRANSCRIPTION_ERROR,
                    file_path=file_path,
                )

                if transcription_result:
                    # Обновляем состояние приложения
                    update_state("file_status", "transcribed")

                    # Загружаем текст транскрипции в состояние
                    transcript_path = get_transcript_file_path(file_path)
                    if os.path.exists(transcript_path):
                        transcript_text = read_transcript(transcript_path)
                        update_state("transcript_text", transcript_text)

                    st.rerun()
        else:
            st.error("Файл не найден. Загрузите файл перед распознаванием.")


def render_transcript_content():
    """Отрисовка содержимого транскрипции"""
    transcript_text = get_state("transcript_text")
    if transcript_text:
        if st.toggle("Результаты распознавания", value=False, key="transcribed_toggle"):
            st.subheader("Результаты распознавания речи")
            # Отображаем текст
            st.text_area(
                "Распознанный текст",
                transcript_text,
                height=250,
                key="transcript_text_area",
            )
            copy_button(transcript_text)
