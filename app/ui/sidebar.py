import streamlit as st


def reset_app_state():
    """Сбрасывает состояние приложения"""
    # Список ключей, которые нужно сохранить (например, настройки)
    keys_to_preserve = ["auto_refresh", "refresh_interval"]

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

    return True


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
                st.cache_data.clear()
                st.success("Кэш очищен")

        # Кнопка сброса состояния
        if st.sidebar.button("Сбросить состояние", key="debug_reset_state_btn"):
            reset_app_state()
            st.sidebar.success("Состояние приложения сброшено")
            st.rerun()

        # Дополнительные инструменты отладки
        if st.sidebar.button("Показать session_state", key="debug_show_state_btn"):
            st.sidebar.write("Session State:")
            st.sidebar.json(dict(st.session_state))

        # Опция очистки логов
        if st.sidebar.button("Очистить лог-файл", key="debug_clear_logs_btn"):
            try:
                # Очистка файла логов
                open("./logs/app.log", "w").close()
                st.sidebar.success("Лог-файл очищен")
            except Exception as e:
                st.sidebar.error(f"Ошибка при очистке лога: {str(e)}")


def setup_sidebar():
    """Настройка и инициализация сайдбара"""
    # Добавляем отладочную панель
    display_debug_panel()

    # Возвращаем пустые значения, так как логи не отображаются
    return None, 0, None
