"""
Модуль для управления файловыми компонентами интерфейса.
Содержит функции для отображения элементов загрузки файлов,
отображения информации о файлах и удаления файлов.
"""

import streamlit as st
import os
from utils.file_handler import save_uploaded_file, format_size
from utils.error_handler import safe_operation, ErrorType
from utils.logger import log_info
from ui.ui_components import display_file_info
from ui.app_state import get_state, update_state, clear_state
from utils.speech_to_text import (
    transcribe_audio,
    get_transcript_file_path,
    get_json_transcript_file_path,
    read_transcript,
)


def render_upload_controls():
    """Отрисовка элементов управления загрузки файла"""
    st.subheader("Загрузка аудиофайла")

    # Создаем загрузчик файлов
    uploaded_file = st.file_uploader("Выберите MP3 файл", type=["mp3"])

    if uploaded_file is not None:
        # Отображаем информацию о загружаемом файле
        st.write(f"Файл: {uploaded_file.name}")

        # Кнопка для обработки файла
        if st.button("Загрузить и обработать", key="upload_button"):
            with st.spinner("Обработка файла..."):
                # Используем safe_operation для обработки ошибок
                file_result = safe_operation(
                    save_uploaded_file,
                    ErrorType.FILE_ERROR,
                    uploaded_file=uploaded_file,
                )

                if file_result:
                    file_path, file_size = file_result

                    # Обновляем состояние приложения
                    update_state("file_path", file_path)
                    update_state("file_size", file_size)
                    update_state("file_status", "uploaded")

                    # Автоматически запускаем распознавание речи
                    log_info("Автоматический запуск распознавания речи")
                    transcription_result = safe_operation(
                        transcribe_audio,
                        ErrorType.TRANSCRIPTION_ERROR,
                        file_path=file_path,
                    )

                    if transcription_result:
                        update_state("file_status", "transcribed")

                        # Загружаем текст транскрипции в состояние
                        transcript_path = get_transcript_file_path(file_path)
                        if os.path.exists(transcript_path):
                            transcript_text = read_transcript(transcript_path)
                            update_state("transcript_text", transcript_text)

                    # Обновляем страницу для отображения изменений
                    st.rerun()


def render_file_info_content():
    """Отрисовка информации о файле"""
    file_path = get_state("file_path")
    file_size = get_state("file_size")

    if file_path and file_size:
        st.subheader("Информация о файле")

        # Отображаем информацию о файле используя компонент из ui_components
        file_name = os.path.basename(file_path)
        formatted_size = format_size(file_size)
        display_file_info(file_name, formatted_size)


def render_delete_controls():
    """Отрисовка элементов управления для удаления файлов"""
    file_status = get_state("file_status")

    if file_status in [
        "uploaded",
        "transcribed",
        "speakers_processed",
        "corrections_processed",
    ]:
        # Определяем текст кнопки в зависимости от состояния
        button_text = (
            "Удалить файл" if file_status == "uploaded" else "Удалить все файлы"
        )
        button_type = "secondary" if file_status == "uploaded" else "primary"

        # Кнопка для удаления файлов
        if st.button(button_text, key="delete_button", type=button_type):
            handle_delete_files()


def handle_delete_files():
    """Обработка удаления файлов"""
    file_path = get_state("file_path")

    if file_path:
        with st.spinner("Удаление файлов..."):
            # Используем safe_operation для обработки ошибок
            result = safe_operation(
                _delete_files_impl,
                ErrorType.FILE_ERROR,
                operation_name="Удаление файлов",
                file_path=file_path,
            )

            if result:
                # Очищаем состояние и обновляем страницу
                clear_state()
                st.rerun()


def _delete_files_impl(file_path):
    """Реализация удаления файлов"""
    # Получаем путь к файлу транскрипции текст и json
    transcript_path = get_transcript_file_path(file_path)
    json_transcript_path = get_json_transcript_file_path(file_path)

    # Удаляем аудиофайл
    if os.path.exists(file_path):
        os.remove(file_path)

    # Удаляем файл транскрипции
    if os.path.exists(transcript_path):
        os.remove(transcript_path)

    # Удаляем файл json транскрипции
    if os.path.exists(json_transcript_path):
        os.remove(json_transcript_path)

    # Также удаляем файлы с обновленной и исправленной транскрипцией, если они существуют
    named_transcript_path = transcript_path.replace(".txt", "_named.txt")
    if os.path.exists(named_transcript_path):
        os.remove(named_transcript_path)

    corrected_transcript_path = transcript_path.replace(".txt", "_corrected.txt")
    if os.path.exists(corrected_transcript_path):
        os.remove(corrected_transcript_path)

    log_info(f"Файлы удалены: {file_path}, {transcript_path}, {json_transcript_path}")
    return True
