"""
Модуль для координации отображения всего приложения.
Содержит главную функцию рендеринга, которая вызывает соответствующие
компоненты в зависимости от текущего состояния приложения.
"""

import streamlit as st
from ui.app_state import initialize_app_state, get_state
from ui.file_components import (
    render_upload_controls,
    render_file_info_content,
    render_delete_controls,
)
from ui.transcription_components import (
    render_transcription_controls,
    render_transcript_content,
)
from ui.speaker_components import (
    render_speaker_define_controls,
    render_speaker_define_content,
)
from ui.correction_components import (
    render_correction_controls,
    render_correction_content,
)


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
