import streamlit as st
from utils.error_handler import safe_operation, ErrorType
from utils.logger import log_info


def reset_app_state():
    """Сбрасывает состояние приложения"""

    def _reset_app_state_impl():
        # Список ключей, которые нужно сохранить (например, настройки)
        keys_to_preserve = ["auto_refresh", "refresh_interval", "config"]

        # Сохраняем значения, которые нужно сохранить
        preserved_values = {}
        for key in keys_to_preserve:
            if key in st.session_state:
                preserved_values[key] = st.session_state[key]

        # Очищаем session_state
        for key in list(st.session_state.keys()):
            if key not in keys_to_preserve:
                del st.session_state[key]

        # Восстанавливаем сохраненные значения
        for key, value in preserved_values.items():
            st.session_state[key] = value

        # Устанавливаем состояние file_status в начальное значение
        st.session_state.file_status = "not_uploaded"

        log_info("Состояние приложения сброшено")

        return True

    # Используем safe_operation для обработки ошибок
    return safe_operation(
        _reset_app_state_impl,
        ErrorType.UNKNOWN_ERROR,
        operation_name="Сброс состояния приложения",
        show_ui_error=True,
    )


def display_debug_panel():
    """Отображение отладочной панели"""
    st.sidebar.title("Отладочная панель")

    if st.sidebar.toggle("Показать инструменты", value=False, key="debug_ctrl_toggle"):
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("Перезапустить", key="debug_restart_btn"):
                st.rerun()

        with col2:
            if st.button("Очистить кэш", key="debug_clear_cache_btn"):
                safe_operation(
                    st.cache_data.clear,
                    ErrorType.UNKNOWN_ERROR,
                    operation_name="Очистка кэша",
                    show_ui_error=True,
                )
                st.success("Кэш очищен")

        # Кнопка сброса состояния
        if st.sidebar.button("Сбросить состояние", key="debug_reset_state_btn"):
            if reset_app_state():
                st.sidebar.success("Состояние приложения сброшено")
                st.rerun()

        # Дополнительные инструменты отладки
        if st.sidebar.button("Показать session_state", key="debug_show_state_btn"):
            st.sidebar.write("Session State:")
            st.sidebar.json(dict(st.session_state))

        # Опция очистки логов
        if st.sidebar.button("Очистить лог-файл", key="debug_clear_logs_btn"):

            def clear_log_file():
                # Очистка файла логов
                open("./logs/app.log", "w").close()
                log_info("Лог-файл очищен")
                return True

            if safe_operation(
                clear_log_file,
                ErrorType.FILE_ERROR,
                operation_name="Очистка лог-файла",
                show_ui_error=True,
            ):
                st.sidebar.success("Лог-файл очищен")

        # Показываем текущую конфигурацию
        if "config" in st.session_state and st.sidebar.button(
            "Показать конфигурацию", key="debug_show_config_btn"
        ):

            config = st.session_state.config

            st.sidebar.subheader("Текущая конфигурация")

            # Показываем API ключи (маскируем их)
            st.sidebar.write("API ключи:")
            for key_name in ["OpenAI", "Anthropic", "Deepseek", "ElevenLabs"]:
                attr_name = f"{key_name.lower()}_api_key"
                key_value = getattr(config, attr_name)
                masked_key = (
                    "Не установлен" if not key_value else "********" + key_value[-4:]
                )
                st.sidebar.text(f"- {key_name}: {masked_key}")

            # Показываем доступных провайдеров
            st.sidebar.write("Доступные провайдеры:")
            for provider in config.available_providers:
                st.sidebar.text(f"- {provider}")

            # Показываем настройки по умолчанию
            st.sidebar.write("Настройки по умолчанию:")
            st.sidebar.text(f"- Провайдер: {config.default_llm_provider}")
            st.sidebar.text(f"- Температура: {config.default_temperature}")
            st.sidebar.text(f"- Макс. токенов: {config.default_max_tokens}")


def setup_sidebar():
    """Настройка и инициализация сайдбара"""
    # Добавляем отладочную панель
    display_debug_panel()

    # Возвращаем пустые значения, так как логи не отображаются
    return None, 0, None
