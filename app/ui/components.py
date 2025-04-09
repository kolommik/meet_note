import streamlit as st
import os
from utils.file_handler import save_uploaded_file, format_size
from utils.speech_to_text import (
    transcribe_audio,
    get_transcript_file_path,
    get_json_transcript_file_path,
    read_transcript,
)
from utils.logger import log_info, log_error


def initialize_app_state():
    """Инициализация состояния приложения"""
    # Инициализируем состояние файла, если оно еще не установлено
    if "file_status" not in st.session_state:
        st.session_state.file_status = "not_uploaded"

    # Инициализируем пути к файлам, если они еще не установлены
    if "file_path" not in st.session_state:
        st.session_state.file_path = None

    if "file_size" not in st.session_state:
        st.session_state.file_size = None


def handle_file_upload(uploaded_file):
    """Обработка загрузки файла"""
    with st.spinner("Обработка файла..."):
        # Сохраняем файл и получаем размер
        file_path, file_size = save_uploaded_file(uploaded_file)

        if file_path:
            # Сохраняем информацию о файле в состоянии
            st.session_state.file_path = file_path
            st.session_state.file_size = file_size
            st.session_state.file_status = "uploaded"

            # Обновляем страницу для отображения изменений
            st.rerun()
        else:
            st.error("Произошла ошибка при загрузке файла")


def handle_transcription():
    """Обработка распознавания речи"""
    if st.session_state.file_path:
        with st.spinner("Распознавание речи..."):

            # Вызываем API для распознавания речи
            transcription_result = transcribe_audio(st.session_state.file_path)

            if transcription_result:
                st.session_state.file_status = "transcribed"
                st.rerun()
            else:
                st.error("Произошла ошибка при распознавании речи")
                log_error("Ошибка при распознавании речи")
    else:
        st.error("Файл не найден. Загрузите файл перед распознаванием.")


def handle_delete_files():
    """Удаление всех файлов"""
    if st.session_state.file_path:
        try:
            # Получаем путь к файлу транскрипции текст и json
            transcript_path = get_transcript_file_path(st.session_state.file_path)
            # Получаем путь к файлу транскрипции
            json_transcript_path = get_json_transcript_file_path(
                st.session_state.file_path
            )

            # Удаляем аудиофайл
            if os.path.exists(st.session_state.file_path):
                os.remove(st.session_state.file_path)

            # Удаляем файл транскрипции
            if os.path.exists(transcript_path):
                os.remove(transcript_path)

            # Удаляем файл транскрипции
            if os.path.exists(json_transcript_path):
                os.remove(json_transcript_path)

            # Обновляем состояние
            st.session_state.file_status = "not_uploaded"
            st.session_state.file_path = None
            st.session_state.file_size = None

            log_info(
                f"Файлы удалены: {st.session_state.file_path}, {transcript_path}, {json_transcript_path}"
            )

            # Обновляем страницу
            st.rerun()
        except Exception as e:
            st.error(f"Произошла ошибка при удалении файлов: {str(e)}")
            log_error(f"Ошибка при удалении файлов: {str(e)}")


def file_upload_section():
    """Секция загрузки файла"""
    # Инициализируем состояние приложения
    initialize_app_state()

    st.title("Загрузка и распознавание аудиофайла")

    # Показываем различные элементы в зависимости от состояния
    if st.session_state.file_status == "not_uploaded":
        # Этап 1: Загрузка файла
        st.write("Загрузите MP3 файл для обработки и распознавания речи")

        # Создаем загрузчик файлов
        uploaded_file = st.file_uploader("Выберите MP3 файл", type=["mp3"])

        if uploaded_file is not None:
            # Отображаем информацию о загружаемом файле
            st.write(f"Файл: {uploaded_file.name}")

            # Кнопка для обработки файла
            if st.button("Загрузить и обработать", key="upload_button"):
                handle_file_upload(uploaded_file)

    elif st.session_state.file_status == "uploaded":
        # Этап 2: Файл загружен, предлагаем распознать речь
        st.write("Файл успешно загружен и готов к обработке")

        # Отображаем информацию о файле
        file_name = os.path.basename(st.session_state.file_path)
        formatted_size = format_size(st.session_state.file_size)

        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.info(f"Файл: {file_name}")
        with info_col2:
            st.info(f"Размер: {formatted_size}")

        # Кнопка для распознавания речи
        if st.button("Распознать речь", key="transcribe_button"):
            handle_transcription()

        # Кнопка для очистки и возврата к загрузке
        if st.button("Удалить файл", key="delete_button"):
            handle_delete_files()

    elif st.session_state.file_status == "transcribed":
        # Этап 3: Речь распознана, отображаем результаты
        st.write("Речь успешно распознана")

        # Отображаем информацию о файле
        file_name = os.path.basename(st.session_state.file_path)
        formatted_size = format_size(st.session_state.file_size)

        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.info(f"Файл: {file_name}")
        with info_col2:
            st.info(f"Размер: {formatted_size}")

        # Получаем путь к файлу транскрипции
        transcript_path = get_transcript_file_path(st.session_state.file_path)

        if os.path.exists(transcript_path):
            # Читаем содержимое файла транскрипции
            transcript_text = read_transcript(transcript_path)

            st.subheader("Результаты распознавания речи")

            # Отображаем текст
            st.text_area(
                "Распознанный текст",
                transcript_text,
                height=250,
                key="transcript_text_area",
            )

            # Добавляем кнопки для скачивания файла и удаления файлов
            col1, col2 = st.columns(2)

            with col1:
                # Кнопка скачивания файла транскрипции
                with open(transcript_path, "rb") as file:
                    st.download_button(
                        label="Скачать файл транскрипции",
                        data=file,
                        file_name=os.path.basename(transcript_path),
                        mime="text/plain",
                        key="download_transcript_button",
                    )

            with col2:
                # Кнопка удаления файлов
                if st.button("Удалить все файлы", key="delete_files_button"):
                    handle_delete_files()
        else:
            st.warning("Файл с результатами распознавания не найден.")

            # Кнопка для очистки и возврата к загрузке
            if st.button("Начать заново", key="restart_button"):
                st.session_state.file_status = "not_uploaded"
                st.session_state.file_path = None
                st.session_state.file_size = None
                st.rerun()
