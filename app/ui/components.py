import streamlit as st
import os
from utils.file_handler import save_uploaded_file, format_size
from utils.speech_to_text import (
    transcribe_audio,
    get_transcript_file_path,
    get_json_transcript_file_path,
    read_transcript,
)
from utils.logger import log_info
from utils.error_handler import safe_operation, ErrorType
from ui.ui_components import (
    copy_button,
    display_file_info,
    display_speaker_statistics,
    display_llm_selector,
    display_analysis_results,
)
from utils.transcript_analysis import (
    calculate_speaker_statistics,
    identify_speakers_with_llm,
)
from utils.config import init_streamlit_config


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

    # Инициализируем переменные для анализа транскрипции
    if "speaker_stats" not in st.session_state:
        st.session_state.speaker_stats = None

    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None

    # Инициализируем переменные для статистики LLM
    if "llm_stats" not in st.session_state:
        st.session_state.llm_stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_create_tokens": 0,
            "cache_read_tokens": 0,
            "full_price": 0.0,
            "model": None,
            "provider": None,
        }

    # Инициализируем конфигурацию, если она еще не установлена
    if "config" not in st.session_state:
        init_streamlit_config()


def handle_file_upload(uploaded_file):
    """Обработка загрузки файла"""
    with st.spinner("Обработка файла..."):
        # Используем safe_operation для обработки ошибок
        file_result = safe_operation(
            save_uploaded_file, ErrorType.FILE_ERROR, uploaded_file=uploaded_file
        )

        if file_result:
            file_path, file_size = file_result

            # Сохраняем информацию о файле в состоянии
            st.session_state.file_path = file_path
            st.session_state.file_size = file_size
            st.session_state.file_status = "uploaded"

            # Обновляем страницу для отображения изменений
            st.rerun()


def handle_transcription():
    """Обработка распознавания речи"""
    if st.session_state.file_path:
        with st.spinner("Распознавание речи..."):
            # Используем safe_operation для обработки ошибок
            transcription_result = safe_operation(
                transcribe_audio,
                ErrorType.TRANSCRIPTION_ERROR,
                file_path=st.session_state.file_path,
            )

            if transcription_result:
                st.session_state.file_status = "transcribed"
                st.rerun()
    else:
        st.error("Файл не найден. Загрузите файл перед распознаванием.")


def handle_delete_files():
    """Удаление всех файлов"""
    if st.session_state.file_path:

        def _delete_files_impl():
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
            st.session_state.speaker_stats = None
            st.session_state.analysis_results = None
            st.session_state.llm_stats = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_create_tokens": 0,
                "cache_read_tokens": 0,
                "full_price": 0.0,
                "model": None,
                "provider": None,
            }

            log_info(
                f"Файлы удалены: {st.session_state.file_path}, {transcript_path}, {json_transcript_path}"
            )
            return True

        # Используем safe_operation для обработки ошибок
        result = safe_operation(
            _delete_files_impl, ErrorType.FILE_ERROR, operation_name="Удаление файлов"
        )

        if result:
            # Обновляем страницу
            st.rerun()


def analyze_transcript(transcript_text):
    """
    Анализирует транскрипцию и отображает статистику по спикерам

    Args:
        transcript_text: Текст транскрипции
    """
    # Подсчитываем статистику спикеров
    with st.spinner("Подсчет статистики спикеров..."):
        speaker_stats = calculate_speaker_statistics(transcript_text)
        st.session_state.speaker_stats = speaker_stats

    # Отображаем базовую статистику используя компонент из ui_components
    st.subheader("Статистика спикеров")
    display_speaker_statistics(speaker_stats)

    # Отображаем секцию для анализа с помощью LLM
    st.subheader("Анализ с помощью LLM")

    # Если конфигурация не инициализирована в session_state, инициализируем
    if "config" not in st.session_state:
        init_streamlit_config()

    config = st.session_state.config

    # Определяем доступных провайдеров из конфигурации
    available_providers = config.available_providers

    if not available_providers:
        st.warning("Не найдено доступных провайдеров LLM. Проверьте файл .env")
        return

    # Используем компонент из ui_components
    llm_provider, model_name, llm_strategy = display_llm_selector(
        available_providers, key_prefix="analysis_"
    )

    if llm_strategy:
        # Кнопка для запуска анализа с помощью LLM
        if st.button("Провести анализ с помощью LLM"):
            with st.spinner("Анализ разговора с помощью LLM..."):

                def _analyze_with_llm():
                    log_info(
                        "Начинаем анализ транскрипции с помощью "
                        + llm_provider
                        + ", модель "
                        + model_name
                    )

                    # Запускаем анализ с помощью LLM
                    analysis_results = identify_speakers_with_llm(
                        transcript_text=transcript_text,
                        speaker_stats=speaker_stats,
                        llm_strategy=llm_strategy,
                        model_name=model_name,
                        max_tokens=4096,  # Увеличиваем максимальное количество токенов для ответа
                    )
                    log_info("Анализ завершен успешно")

                    # Сохраняем результаты анализа в сессии
                    st.session_state.analysis_results = analysis_results

                    # Сохраняем статистику использования модели
                    st.session_state.llm_stats = {
                        "input_tokens": llm_strategy.get_input_tokens(),
                        "output_tokens": llm_strategy.get_output_tokens(),
                        "cache_create_tokens": llm_strategy.get_cache_create_tokens(),
                        "cache_read_tokens": llm_strategy.get_cache_read_tokens(),
                        "full_price": llm_strategy.get_full_price(),
                        "model": model_name,
                        "provider": llm_provider,
                    }

                    # Возвращаем результаты анализа
                    return analysis_results

                # Используем safe_operation для обработки ошибок
                analysis_results = safe_operation(
                    _analyze_with_llm,
                    ErrorType.LLM_ERROR,
                    operation_name="Анализ с помощью LLM",
                    show_ui_error=True,
                )

                # Если анализ успешно выполнен, отображаем результаты
                if analysis_results:
                    # Используем компонент из ui_components для отображения результатов
                    display_analysis_results(analysis_results)
    else:
        st.info("Для анализа транскрипции укажите API ключ и выберите модель LLM")


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

        # Отображаем информацию о файле используя компонент из ui_components
        file_name = os.path.basename(st.session_state.file_path)
        formatted_size = format_size(st.session_state.file_size)
        display_file_info(file_name, formatted_size)

        # Кнопка для распознавания речи
        if st.button("Распознать речь", key="transcribe_button"):
            handle_transcription()

        # Кнопка для очистки и возврата к загрузке
        if st.button("Удалить файл", key="delete_button"):
            handle_delete_files()

    elif st.session_state.file_status == "transcribed":
        # Этап 3: Речь распознана, отображаем результаты
        st.write("Речь успешно распознана")

        # Отображаем информацию о файле используя компонент из ui_components
        file_name = os.path.basename(st.session_state.file_path)
        formatted_size = format_size(st.session_state.file_size)
        display_file_info(file_name, formatted_size)

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

            copy_button(transcript_text)

            # Создаем вкладки для основного контента и анализа
            tab1, tab2 = st.tabs(["Скачать и управлять", "Анализ транскрипции"])

            with tab1:
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

            with tab2:
                # Запускаем анализ транскрипции
                analyze_transcript(transcript_text)

        else:
            st.warning("Файл с результатами распознавания не найден.")

            # Кнопка для очистки и возврата к загрузке
            if st.button("Начать заново", key="restart_button"):
                st.session_state.file_status = "not_uploaded"
                st.session_state.file_path = None
                st.session_state.file_size = None
                st.rerun()
