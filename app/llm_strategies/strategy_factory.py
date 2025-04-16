"""
Фабричный модуль для создания и инициализации стратегий LLM.
Предоставляет простой интерфейс для получения нужной стратегии
без знания деталей их создания и инициализации.
"""

from llm_strategies.chat_model_strategy import ChatModelStrategy
from llm_strategies.anthropic_strategy import AnthropicChatStrategy
from llm_strategies.openai_strategy import OpenAIChatStrategy
from llm_strategies.deepseek_strategy import DeepseekChatStrategy


def create_strategy(provider: str, api_key: str) -> ChatModelStrategy:
    """
    Создает и возвращает стратегию для работы с указанным провайдером LLM.

    Parameters
    ----------
    provider : str
        Название провайдера LLM ('anthropic', 'openai', 'deepseek')
    api_key : str
        API ключ для доступа к провайдеру

    Returns
    -------
    ChatModelStrategy
        Инициализированная стратегия для работы с указанным провайдером

    Raises
    ------
    ValueError
        Если указан неизвестный провайдер
    """
    provider = provider.lower()

    if provider == "anthropic":
        return AnthropicChatStrategy(api_key)
    elif provider == "openai":
        return OpenAIChatStrategy(api_key)
    elif provider == "deepseek":
        return DeepseekChatStrategy(api_key)
    else:
        raise ValueError(f"Неизвестный провайдер LLM: {provider}")


def get_available_providers() -> list[str]:
    """
    Возвращает список доступных провайдеров LLM.

    Returns
    -------
    list[str]
        Список названий доступных провайдеров
    """
    return ["anthropic", "openai", "deepseek"]
