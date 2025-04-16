"""
Базовый класс для стратегий взаимодействия с LLM API.
Реализует общую функциональность для всех стратегий и определяет
абстрактные методы, которые должны быть реализованы в конкретных стратегиях.
"""

from abc import abstractmethod
from typing import List, Dict
from llm_strategies.chat_model_strategy import ChatModelStrategy


class BaseChatModelStrategy(ChatModelStrategy):
    """
    Базовый класс для всех стратегий взаимодействия с LLM API.

    Содержит общую функциональность и структуру для конкретных стратегий,
    что позволяет избежать дублирования кода.

    Parameters
    ----------
    api_key : str
        API ключ для доступа к LLM API.

    Attributes
    ----------
    api_key : str
        API ключ для доступа к LLM API.
    models : List[Model]
        Список доступных моделей для данной стратегии.
    input_tokens : int
        Количество входных токенов, использованных в последнем запросе.
    output_tokens : int
        Количество выходных токенов, сгенерированных в последнем ответе.
    cache_create_tokens : int
        Количество токенов, используемых для создания кэша.
    cache_read_tokens : int
        Количество токенов, прочитанных из кэша.
    model : str
        Название модели, используемой в последнем запросе.
    """

    def __init__(self, api_key: str):
        """
        Инициализирует базовую стратегию с общими атрибутами.

        Parameters
        ----------
        api_key : str
            API ключ для доступа к LLM API.
        """
        self.api_key = api_key
        self.models = []  # Будет заполнено в конкретных реализациях
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_create_tokens = 0
        self.cache_read_tokens = 0
        self.model = None

    def get_models(self) -> List[str]:
        """
        Возвращает список доступных моделей для данной стратегии.

        Returns
        -------
        List[str]
            Список названий доступных моделей.
        """
        return [model.name for model in self.models]

    def get_output_max_tokens(self, model_name: str) -> int:
        """
        Возвращает максимальное количество выходных токенов для указанной модели.

        Parameters
        ----------
        model_name : str
            Название модели.

        Returns
        -------
        int
            Максимальное количество выходных токенов для указанной модели.
        """
        return self.models[self.get_models().index(model_name)].output_max_tokens

    def get_input_tokens(self) -> int:
        """
        Возвращает количество входных токенов, использованных в последнем запросе.

        Returns
        -------
        int
            Количество входных токенов.
        """
        return self.input_tokens

    def get_output_tokens(self) -> int:
        """
        Возвращает количество выходных токенов, сгенерированных в последнем ответе.

        Returns
        -------
        int
            Количество выходных токенов.
        """
        return self.output_tokens

    def get_cache_create_tokens(self) -> int:
        """
        Возвращает количество токенов, использованных для создания кэша.

        Returns
        -------
        int
            Количество токенов создания кэша.
        """
        return self.cache_create_tokens

    def get_cache_read_tokens(self) -> int:
        """
        Возвращает количество токенов, прочитанных из кэша.

        Returns
        -------
        int
            Количество токенов чтения из кэша.
        """
        return self.cache_read_tokens

    def get_full_price(self) -> float:
        """
        Рассчитывает и возвращает полную стоимость на основе входных и выходных токенов.

        Базовая реализация учитывает стандартное ценообразование, конкретные стратегии
        могут переопределить этот метод при необходимости.

        Returns
        -------
        float
            Полная стоимость запроса в долларах США.
        """
        # Проверяем, инициализирована ли модель
        if self.model is None:
            return 0.0  # Возвращаем 0, если модель не определена

        model_index = self.get_models().index(self.model)
        model_info = self.models[model_index]

        # Базовая стоимость входных токенов
        inputs = self.input_tokens * model_info.price_input / 1_000_000.0

        # Базовая стоимость выходных токенов
        outputs = self.output_tokens * model_info.price_output / 1_000_000.0

        # Базовая стоимость токенов создания кэша
        # По умолчанию равна стоимости входных токенов
        cache_create = self.cache_create_tokens * model_info.price_input / 1_000_000.0

        # Базовая стоимость токенов чтения из кэша
        # По умолчанию составляет 10% от стоимости входных токенов
        cache_read = self.cache_read_tokens * model_info.price_input * 0.1 / 1_000_000.0

        return inputs + outputs + cache_create + cache_read

    @abstractmethod
    def send_message(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model_name: str,
        max_tokens: int,
        temperature: float = 0,
    ) -> str:
        """
        Отправляет сообщение к LLM API и возвращает сгенерированный ответ.

        Этот метод должен быть реализован в конкретных стратегиях.

        Parameters
        ----------
        system_prompt : str
            Системный промпт для контекста разговора.
        messages : List[Dict[str, str]]
            Список сообщений в разговоре, каждое представлено в виде словаря.
        model_name : str
            Название модели для генерации ответа.
        max_tokens : int
            Максимальное количество токенов для генерации в ответе.
        temperature : float, optional
            Температура генерации (случайность ответа), по умолчанию 0.

        Returns
        -------
        str
            Сгенерированный ответ от LLM API.
        """
        pass
