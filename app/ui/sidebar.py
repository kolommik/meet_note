import streamlit as st
from utils.error_handler import safe_operation, ErrorType
from utils.logger import log_info
from utils.llm_stats import get_total_llm_stats, reset_llm_stats
from ui.app_state import update_state


def reset_app_state():
    """Сбрасывает состояние приложения"""

    def _reset_app_state_impl():
        # Список ключей, которые нужно сохранить (например, настройки)
        keys_to_preserve = [
            "auto_refresh",
            "refresh_interval",
            "config",
            "llm_settings",
        ]

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

        # Сбрасываем статистику LLM
        reset_llm_stats()

        log_info("Состояние приложения сброшено")

        return True

    # Используем safe_operation для обработки ошибок
    return safe_operation(
        _reset_app_state_impl,
        ErrorType.UNKNOWN_ERROR,
        operation_name="Сброс состояния приложения",
        show_ui_error=True,
    )


def display_llm_settings():
    """Отображение панели настроек моделей LLM"""
    if st.sidebar.toggle(
        "Настройки моделей LLM", value=True, key="llm_settings_toggle"
    ):
        st.sidebar.subheader("Настройки моделей LLM")

        # Если конфигурация не инициализирована в session_state, инициализируем
        config = st.session_state.config

        # Определяем доступных провайдеров из конфигурации
        available_providers = config.available_providers

        if not available_providers:
            st.sidebar.warning(
                "Не найдено доступных провайдеров LLM. Проверьте файл .env"
            )
        else:
            # Выбор провайдера LLM
            provider = st.sidebar.selectbox(
                "Провайдер LLM",
                available_providers,
                index=(
                    available_providers.index(
                        st.session_state.llm_settings.get(
                            "provider", available_providers[0]
                        )
                    )
                    if st.session_state.llm_settings.get("provider")
                    in available_providers
                    else 0
                ),
            )

            # Сохраняем выбранного провайдера
            st.session_state.llm_settings["provider"] = provider

            # Определяем модели для выбранного провайдера
            if provider == "Anthropic":
                from llm_strategies.anthropic_strategy import AnthropicChatStrategy

                api_key = config.anthropic_api_key
                llm_strategy = AnthropicChatStrategy(api_key)
            elif provider == "OpenAI":
                from llm_strategies.openai_strategy import OpenAIChatStrategy

                api_key = config.openai_api_key
                llm_strategy = OpenAIChatStrategy(api_key)
            else:  # Deepseek
                from llm_strategies.deepseek_strategy import DeepseekChatStrategy

                api_key = config.deepseek_api_key
                llm_strategy = DeepseekChatStrategy(api_key)

            # Получаем список моделей
            model_options = llm_strategy.get_models()

            # Выбор модели
            model_index = 0
            if st.session_state.llm_settings.get("model") in model_options:
                model_index = model_options.index(
                    st.session_state.llm_settings.get("model")
                )

            model = st.sidebar.selectbox("Модель LLM", model_options, index=model_index)

            # Сохраняем выбранную модель
            st.session_state.llm_settings["model"] = model

            # Сохраняем стратегию для использования в других частях приложения
            st.session_state.llm_settings["strategy"] = llm_strategy

        # Ползунок для температуры
        st.session_state.llm_settings["temperature"] = st.sidebar.slider(
            "Температура",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.llm_settings.get("temperature", 0.0),
            step=0.1,
            help="Регулирует случайность генерации. Низкие значения делают ответ более детерминированным.",
        )

        # Поле для ввода максимального количества токенов

        model_max_tokens = llm_strategy.get_output_max_tokens(model)
        model_min_tokens = 4096
        model_current_tokens = st.session_state.llm_settings.get("max_tokens", 4096)
        if model_current_tokens > model_max_tokens:
            model_current_tokens = model_max_tokens
        st.session_state.llm_settings["max_tokens"] = st.sidebar.number_input(
            "Макс. токенов",
            min_value=model_min_tokens,
            max_value=model_max_tokens,
            value=model_current_tokens,
            step=512,
            help="Максимальное количество токенов в ответе LLM",
        )

        # Отображаем текущие настройки
        st.sidebar.info(
            f"Текущие настройки:\n"
            f"- Провайдер: {st.session_state.llm_settings.get('provider', 'Не выбран')}\n"
            f"- Модель: {st.session_state.llm_settings.get('model', 'Не выбрана')}\n"
            f"- Температура: {st.session_state.llm_settings['temperature']}\n"
            f"- Макс. токенов: {st.session_state.llm_settings['max_tokens']}"
        )


def display_llm_stats():
    """Отображение статистики использования LLM"""
    st.sidebar.markdown("---")

    # Получаем общую статистику
    total_stats = get_total_llm_stats()

    if st.sidebar.toggle("Метрики", value=True, key="full_price_toggle"):
        st.sidebar.metric("Полная стоимость", f"{100*total_stats['total_cost']:.4f}¢")

    if "llm_stats" in st.session_state and st.sidebar.toggle(
        "Статистика LLM", value=False, key="llm_stats_toggle"
    ):
        stats = st.session_state.llm_stats

        st.sidebar.subheader("Статистика использования LLM")

        if stats.get("model"):
            st.sidebar.markdown("**Последний запрос:**")
            st.sidebar.markdown(f"**Модель:** {stats['model']}")

            # Токены последнего запроса
            st.sidebar.markdown("### Токены (последний запрос)")
            st.sidebar.markdown(f"- Входные: {stats['input_tokens']}")
            st.sidebar.markdown(f"- Выходные: {stats['output_tokens']}")
            st.sidebar.markdown(f"- Создание кэша: {stats['cache_create_tokens']}")
            st.sidebar.markdown(f"- Чтение из кэша: {stats['cache_read_tokens']}")
            total_tokens = (
                stats["input_tokens"]
                + stats["output_tokens"]
                + stats["cache_create_tokens"]
                + stats["cache_read_tokens"]
            )
            st.sidebar.markdown(f"- Всего: {total_tokens}")

            # Стоимость последнего запроса
            st.sidebar.markdown("### Стоимость (последний запрос)")
            st.sidebar.markdown(f"- Общая: ${stats['full_price']:.6f}")

            # Общая статистика за всю сессию
            st.sidebar.markdown("---")
            st.sidebar.markdown("## Общая статистика за сессию")
            st.sidebar.markdown(f"- Всего запросов: {total_stats['total_calls']}")
            st.sidebar.markdown(
                f"- Всего входных токенов: {total_stats['total_input_tokens']}"
            )
            st.sidebar.markdown(
                f"- Всего выходных токенов: {total_stats['total_output_tokens']}"
            )
            st.sidebar.markdown(
                f"- Всего токенов создания кэша: {total_stats['total_cache_create_tokens']}"
            )
            st.sidebar.markdown(
                f"- Всего токенов чтения из кэша: {total_stats['total_cache_read_tokens']}"
            )
            st.sidebar.markdown(
                f"- **Общая стоимость**: ${total_stats['total_cost']:.6f}"
            )
        else:
            st.sidebar.info("Статистика LLM будет доступна после использования модели")


def display_debug_panel():
    """Отображение отладочной панели"""
    st.sidebar.markdown("---")
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

        # Кнопка сброса статуса
        if st.sidebar.button(
            "Сбросить статус последнего шага", key="debug_reset_file_status_btn"
        ):
            update_state("file_status", "corrections_processed")
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
    # Добавляем настройки моделей LLM
    display_llm_settings()

    # Добавляем статистику LLM
    display_llm_stats()

    # Добавляем отладочную панель
    display_debug_panel()
