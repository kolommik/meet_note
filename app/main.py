import streamlit as st
from ui.main_renderer import render_main_page
from ui.sidebar import setup_sidebar
from utils.logger import log_info
from utils.error_handler import safe_operation, ErrorType
from utils.config import init_streamlit_config


def main():
    """Основная функция приложения"""

    def _setup_app():
        # Настраиваем страницу
        st.set_page_config(
            page_title="Meet Note",
            page_icon="✍️",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Логируем запуск приложения только при первом запуске
        if "app_initialized" not in st.session_state:
            log_info("Application started")
            st.session_state.app_initialized = True

        # Инициализируем конфигурацию только если её нет
        if "config" not in st.session_state:
            init_streamlit_config()
            log_info("Конфигурация приложения инициализирована")

        # Настраиваем сайдбар и основной контент
        setup_sidebar()
        render_main_page()

        return True

    # Используем safe_operation для обработки ошибок
    safe_operation(
        _setup_app,
        ErrorType.UNKNOWN_ERROR,
        operation_name="Инициализация приложения",
        show_ui_error=True,
    )


if __name__ == "__main__":
    main()
