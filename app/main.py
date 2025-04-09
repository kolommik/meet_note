import streamlit as st
from ui.components import file_upload_section
from ui.sidebar import setup_sidebar
from utils.logger import log_info


def main():
    # Настраиваем страницу
    st.set_page_config(
        page_title="MP3 File Processor",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Логируем запуск приложения
    log_info("Application started")

    try:
        # Настраиваем сайдбар с отладочной панелью
        setup_sidebar()

        # Основная секция для загрузки файла
        file_upload_section()

    except KeyboardInterrupt:
        log_info("Application stopped")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        log_info(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
