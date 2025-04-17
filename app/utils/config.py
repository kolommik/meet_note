from dataclasses import dataclass, field
from typing import Optional, List
import os
from dotenv import load_dotenv
from utils.error_handler import ErrorType, handle_error
import streamlit as st

# Глобальный экземпляр конфигурации (для паттерна Синглтон)
_config_instance = None


@dataclass
class AppConfig:
    """Конфигурация приложения с валидацией и значениями по умолчанию."""

    # API ключи
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None

    # Пути к директориям
    data_dir: str = "./data"
    context_dir: str = "./context"

    # Настройки по умолчанию для LLM
    default_llm_provider: str = "Anthropic"
    default_temperature: float = 0.0
    default_max_tokens: int = 4096

    # Настройки для транскрипции (Не используется)
    max_speakers: int = 10

    # Доступные LLM провайдеры
    available_providers: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Валидация после инициализации."""
        try:
            # Формируем список доступных провайдеров
            self.available_providers = []
            if self.anthropic_api_key:
                self.available_providers.append("Anthropic")
            if self.openai_api_key:
                self.available_providers.append("OpenAI")
            if self.deepseek_api_key:
                self.available_providers.append("Deepseek")
        except Exception as e:
            handle_error(
                ErrorType.CONFIG_ERROR, e, show_ui_error=True, default_return=None
            )

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Создает конфигурацию из переменных окружения.

        Returns:
            AppConfig: Экземпляр конфигурации
        """
        try:
            load_dotenv()

            return cls(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
                elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
                data_dir=os.getenv("DATA_DIR", "./data"),
            )
        except Exception as e:
            handle_error(
                ErrorType.CONFIG_ERROR, e, show_ui_error=True, default_return=None
            )
            # Fallback на дефолтные настройки при ошибке
            return cls()


def get_config() -> AppConfig:
    """
    Получить глобальный экземпляр конфигурации.
    Реализует паттерн Синглтон для доступа к конфигурации из любого модуля.

    Returns:
        AppConfig: Экземпляр конфигурации
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig.from_env()

        # Создаем директории только один раз при первой инициализации
        try:
            os.makedirs(_config_instance.data_dir, exist_ok=True)
        except Exception as e:
            handle_error(
                ErrorType.CONFIG_ERROR,
                Exception(f"Ошибка при создании директорий: {str(e)}"),
                show_ui_error=True,
            )

    return _config_instance


def init_streamlit_config():
    """
    Инициализирует конфигурацию в Streamlit session_state.
    Вызывается из основного файла приложения.
    """
    st.session_state.config = get_config()

    # Инициализируем настройки LLM, если они еще не установлены
    if "llm_settings" not in st.session_state:
        st.session_state.llm_settings = {
            "temperature": st.session_state.config.default_temperature,
            "max_tokens": st.session_state.config.default_max_tokens,
        }
