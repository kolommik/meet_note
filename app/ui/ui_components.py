import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, List, Tuple, Optional
from utils.config import init_streamlit_config


def copy_button(text_to_copy: str, title: str = "Скопировать"):
    """
    Создает кнопку с помощью HTML и JavaScript.
    Копирует переданный текст в буфер обмена при нажатии.
    """
    html_code = f"""
    <div style="margin-top:10px;">
        <button onclick="copyToClipboard()" style="
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 4px;">
            {title}
        </button>
    </div>
    <script>
      function copyToClipboard() {{
          // Создаем временный textarea элемент
          const textarea = document.createElement('textarea');
          textarea.value = `{text_to_copy}`;
          textarea.style.position = 'fixed';  // Предотвращаем прокрутку до элемента
          textarea.style.opacity = '0';  // Делаем элемент невидимым
          document.body.appendChild(textarea);

          try {{
              // Выделяем и копируем текст
              textarea.select();
              document.execCommand('copy');
              alert('Текст скопирован в буфер обмена!');
          }} catch (err) {{
              alert('Не удалось скопировать текст: ' + err);
          }} finally {{
              // Удаляем временный элемент
              document.body.removeChild(textarea);
          }}
      }}
    </script>
    """
    components.html(html_code, height=60)


def display_file_info(file_name: str, file_size: str):
    """
    Отображает информацию о файле в UI.

    Args:
        file_name: Имя файла
        file_size: Отформатированный размер файла
    """
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.info(f"Файл: {file_name}")
    with info_col2:
        st.info(f"Размер: {file_size}")


def display_speaker_statistics(speaker_stats: Dict[str, Dict[str, Any]]):
    """
    Отображает статистику по спикерам в виде таблицы.

    Args:
        speaker_stats: Словарь со статистикой по спикерам
    """
    st.subheader("Статистика спикеров")

    # Создаем таблицу статистики
    stats_data = []
    for speaker, data in speaker_stats.items():
        if speaker != "total":
            stats_data.append(
                {
                    "Спикер": speaker,
                    "Слов": data["word_count"],
                    "Доля в разговоре (%)": data["percentage"],
                    "Высказываний": data["utterances"],
                }
            )

    # Отображаем таблицу
    st.table(stats_data)


def display_llm_selector(
    available_providers: List[str], key_prefix: str = ""
) -> Tuple[Optional[str], Optional[str], Optional[Any]]:
    """
    Отображает UI для выбора провайдера LLM и модели.
    Эта функция используется только если в sidebar не выбраны настройки LLM.

    Args:
        available_providers: Список доступных провайдеров
        key_prefix: Префикс для ключей элементов UI

    Returns:
        tuple: (выбранный провайдер, выбранная модель, экземпляр стратегии)
    """
    if not available_providers:
        st.warning("Не найдено доступных провайдеров LLM. Проверьте файл .env")
        return None, None, None

    st.info(
        "Рекомендуется настроить LLM в боковой панели (меню 'Настройки моделей LLM')"
    )

    # Выбор стратегии LLM из доступных провайдеров
    llm_provider = st.selectbox(
        "Выберите провайдера LLM", available_providers, key=f"{key_prefix}llm_provider"
    )

    # Определяем API ключ и стратегию
    api_key = None
    llm_strategy = None

    # Инициализируем выбранную стратегию
    try:
        # Если конфигурация не инициализирована в session_state, инициализируем
        if "config" not in st.session_state:
            init_streamlit_config()

        config = st.session_state.config

        if llm_provider == "Anthropic":
            from llm_strategies.anthropic_strategy import AnthropicChatStrategy

            api_key = config.anthropic_api_key
            llm_strategy = AnthropicChatStrategy(api_key)
        elif llm_provider == "OpenAI":
            from llm_strategies.openai_strategy import OpenAIChatStrategy

            api_key = config.openai_api_key
            llm_strategy = OpenAIChatStrategy(api_key)
        else:  # Deepseek
            from llm_strategies.deepseek_strategy import DeepseekChatStrategy

            api_key = config.deepseek_api_key
            llm_strategy = DeepseekChatStrategy(api_key)

        model_options = llm_strategy.get_models()

        # Выбор модели
        model_name = st.selectbox(
            "Выберите модель", model_options, key=f"{key_prefix}llm_model"
        )

        # Отображаем текущие настройки из sidebar, если они установлены
        if "llm_settings" in st.session_state:
            st.info(
                f"Настройки модели:\n"
                f"- Температура: {st.session_state.llm_settings.get('temperature', 0.0)}\n"
                f"- Макс. токенов: {st.session_state.llm_settings.get('max_tokens', 1024)}"
            )

        return llm_provider, model_name, llm_strategy

    except Exception as e:
        from utils.error_handler import handle_error, ErrorType

        handle_error(ErrorType.LLM_ERROR, e)
        return None, None, None


def display_analysis_results(analysis_results: Dict[str, Any]):
    """
    Отображает результаты анализа транскрипции.

    Args:
        analysis_results: Результаты анализа
    """
    if "error" in analysis_results:
        st.error(f"Ошибка анализа: {analysis_results['error']}")
        return

    st.markdown("## Результаты анализа транскрипции\n")

    # Добавляем общее описание
    if "summary" in analysis_results:
        st.markdown(f"### Тема разговора\n{analysis_results['summary']}\n")

    # Добавляем информацию о спикерах
    st.markdown("### Информация о спикерах\n")

    for speaker_id, speaker_info in analysis_results.get("speakers", {}).items():
        expander = st.expander(
            f"{speaker_id}: {speaker_info.get('name', 'Неизвестно')}"
        )
        with expander:
            st.markdown(f"**Роль:** {speaker_info.get('role', 'Не определена')}")
            st.markdown(
                f"**Уверенность:** {speaker_info.get('confidence', 'Не указана')}"
            )

            # Добавляем статистику, если она есть
            if "statistics" in speaker_info:
                stats = speaker_info["statistics"]
                st.markdown("**Статистика:**")
                st.markdown(f"- Слов: {stats.get('word_count', 'Н/Д')}")
                st.markdown(f"- Доля в разговоре: {stats.get('percentage', 'Н/Д')}%")
                st.markdown(f"- Высказываний: {stats.get('utterances', 'Н/Д')}")
