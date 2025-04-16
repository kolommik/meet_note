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
)
from utils.transcript_analysis import (
    calculate_speaker_statistics,
    identify_speakers_with_llm,
    identify_corrections_with_llm,
)
from utils.speaker_editor import display_speaker_editor
from utils.correction_editor import display_correction_editor
from utils.config import init_streamlit_config


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

    # LLM настройки и статистика
    if "llm_settings" not in st.session_state:
        st.session_state.llm_settings = {"temperature": 0.0, "max_tokens": 1024}
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


def update_state(key, value):
    """Обновление состояния приложения"""
    st.session_state[key] = value


def get_state(key, default=None):
    """Получение значения из состояния приложения"""
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
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Возвращаем к начальному состоянию
    st.session_state.file_status = "not_uploaded"


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
        if st.toggle("Результаты распознавания", value=True, key="transcribed_toggle"):
            st.subheader("Результаты распознавания речи")
            # Отображаем текст
            st.text_area(
                "Распознанный текст",
                transcript_text,
                height=250,
                key="transcript_text_area",
            )
            copy_button(transcript_text)


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
    "Показываем результаты с исправлениями имен спикеров"
    speaker_updated_text = get_state("speaker_updated_transcript")
    if speaker_updated_text:
        if st.toggle(
            "Транскрипция с именами спикеров", value=True, key="speaker_define_toggle"
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

    # Путь к контекстному файлу
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
    data_dir = os.path.join(app_dir, "..", "data")  # ../data/
    context_dir = os.path.join(data_dir, "context")  # ../data/context/
    context_file = os.path.join(context_dir, "terms.md")

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
            "Контекстный файл не найден. Создайте файл data/context/terms.md \
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
    if st.toggle("Исправленная транскрипция", value=True, key="correction_toggle"):
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


def _define_speakers_with_llm(transcript_text, speaker_stats, llm_strategy, model_name):
    """Анализ транскрипции с помощью LLM"""
    # Получаем настройки LLM из session_state или используем значения по умолчанию
    llm_settings = get_state("llm_settings", {})
    llm_provider = llm_settings.get("provider")
    temperature = llm_settings.get("temperature", 0.0)
    max_tokens = llm_settings.get("max_tokens", 1024)

    # Запускаем анализ с помощью LLM с параметрами из настроек
    analysis_results = identify_speakers_with_llm(
        transcript_text=transcript_text,
        speaker_stats=speaker_stats,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Данные о стоимости для текущего запроса
    current_input_tokens = llm_strategy.get_input_tokens()
    current_output_tokens = llm_strategy.get_output_tokens()
    current_price = llm_strategy.get_full_price()

    # Обновляем общую статистику за сессию
    if "total_llm_cost" not in st.session_state:
        st.session_state.total_llm_cost = 0.0
        st.session_state.total_input_tokens = 0
        st.session_state.total_output_tokens = 0
        st.session_state.total_calls = 0

    st.session_state.total_llm_cost += current_price
    st.session_state.total_input_tokens += current_input_tokens
    st.session_state.total_output_tokens += current_output_tokens
    st.session_state.total_calls += 1

    # Обновляем статистику LLM
    llm_stats = {
        "input_tokens": current_input_tokens,
        "output_tokens": current_output_tokens,
        "cache_create_tokens": llm_strategy.get_cache_create_tokens(),
        "cache_read_tokens": llm_strategy.get_cache_read_tokens(),
        "full_price": current_price,
        "model": model_name,
        "provider": llm_provider,
    }
    update_state("llm_stats", llm_stats)

    return analysis_results


def _identify_corrections_with_llm(
    transcript_text, context_text, llm_strategy, model_name
):
    """Анализ ошибок распознавания с помощью LLM"""
    # Получаем настройки LLM из session_state или используем значения по умолчанию
    llm_settings = get_state("llm_settings", {})
    llm_provider = llm_settings.get("provider")
    temperature = llm_settings.get("temperature", 0.0)
    max_tokens = llm_settings.get("max_tokens", 1024)

    # Запускаем анализ с помощью LLM с параметрами из настроек
    correction_results = identify_corrections_with_llm(
        transcript_text=transcript_text,
        context_text=context_text,
        llm_strategy=llm_strategy,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Данные о стоимости для текущего запроса
    current_input_tokens = llm_strategy.get_input_tokens()
    current_output_tokens = llm_strategy.get_output_tokens()
    current_price = llm_strategy.get_full_price()

    # Обновляем общую статистику за сессию
    if "total_llm_cost" not in st.session_state:
        st.session_state.total_llm_cost = 0.0
        st.session_state.total_input_tokens = 0
        st.session_state.total_output_tokens = 0
        st.session_state.total_calls = 0

    st.session_state.total_llm_cost += current_price
    st.session_state.total_input_tokens += current_input_tokens
    st.session_state.total_output_tokens += current_output_tokens
    st.session_state.total_calls += 1

    # Обновляем статистику LLM
    llm_stats = {
        "input_tokens": current_input_tokens,
        "output_tokens": current_output_tokens,
        "cache_create_tokens": llm_strategy.get_cache_create_tokens(),
        "cache_read_tokens": llm_strategy.get_cache_read_tokens(),
        "full_price": current_price,
        "model": model_name,
        "provider": llm_provider,
    }
    update_state("llm_stats", llm_stats)

    return correction_results


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


def render_main_page():
    """Главный координатор отображения приложения"""
    # Инициализируем состояние приложения
    initialize_app_state()

    st.title("Обработка и анализ аудиофайлов")

    # Получаем текущее состояние
    file_status = get_state("file_status")

    # Шаг 1: Загрузка аудио
    if file_status == "not_uploaded":
        render_upload_controls()
    else:
        render_file_info_content()

    # Шаг 2: Транскрипция
    if file_status == "uploaded":
        render_transcription_controls()
    else:
        render_transcript_content()

    # Шаг 3: Назначим спикеров
    if file_status == "transcribed":
        render_speaker_define_controls()
    else:
        render_speaker_define_content()

    # Шаг 4: Исправление ошибок распознавания
    if file_status == "speakers_processed":
        render_correction_controls()
    else:
        if file_status == "corrections_processed":
            render_correction_content()

    if file_status in [
        "uploaded",
        "transcribed",
        "speakers_processed",
        "corrections_processed",
    ]:
        st.markdown("---")
        render_delete_controls()
