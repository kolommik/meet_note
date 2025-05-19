"""
Базовый класс для стратегий взаимодействия с LLM API.
Реализует общую функциональность для всех стратегий и определяет
абстрактные методы, которые должны быть реализованы в конкретных стратегиях.
"""

from abc import abstractmethod
from typing import List, Dict, Tuple, Optional
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
        # Проверка, существует ли модель
        available_models = self.get_models()
        if model_name not in available_models:
            # Можно выбросить ошибку или вернуть значение по умолчанию/для первой модели
            # ValueError(f"Модель '{model_name}' не найдена в списке доступных для этой стратегии.")
            # Для безопасности, вернем 0 или значение для первой модели, если есть
            if not self.models:
                return 0
            return self.models[
                0
            ].output_max_tokens  # Не очень хорошо, но лучше чем ошибка если не критично

        return self.models[available_models.index(model_name)].output_max_tokens

    def get_input_tokens(self) -> int:
        """
        Возвращает количество входных токенов, использованных в последнем API-запросе.

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
        if self.model is None or not self.models:
            return 0.0

        try:
            model_index = self.get_models().index(self.model)
            model_info = self.models[model_index]
        except ValueError:  # Если self.model не найден в списке
            return 0.0

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
    ) -> Tuple[str, Optional[str]]:
        """
        Отправляет одиночное сообщение к API чат-модели и возвращает сгенерированный ответ
        и причину завершения генерации.

        Этот метод должен быть реализован в конкретных стратегиях.
        Он также должен обновлять self.input_tokens, self.output_tokens, и т.д.
        для ЕДИНИЧНОГО вызова.

        Parameters
        ----------
        system_prompt : str
            Системный промпт для контекста разговора.
        messages : List[Dict[str, str]]
            Список сообщений в разговоре (только user/assistant).
        model_name : str
            Название модели для генерации ответа.
        max_tokens : int
            Максимальное количество токенов для генерации в ответе.
        temperature : float, optional
            Температура генерации (случайность ответа), по умолчанию 0.

        Returns
        -------
        Tuple[str, Optional[str]]
            Кортеж: (сгенерированный ответ от API чат-модели, причина завершения генерации).
        """
        pass

    @abstractmethod
    def generate_full_response(
        self,
        system_prompt: str,
        initial_user_message: str,
        model_name: str,
        max_tokens_per_chunk: int,
        temperature: float,
        max_continuation_attempts: int = 3,
        continuation_prompt_template: str = "Please continue exactly from where it left off.",
    ) -> str:
        """
        Отправляет начальное сообщение и, при необходимости, автоматически обрабатывает
        продолжения для получения полного ответа от LLM, если ответ обрывается из-за лимита токенов.

        Агрегирует статистику по токенам за все вызовы.

        Parameters
        ----------
        system_prompt : str
            Системный промпт.
        initial_user_message : str
            Начальное сообщение от пользователя.
        model_name : str
            Название модели.
        max_tokens_per_chunk : int
            Максимальное количество токенов для генерации в каждом отдельном запросе к API.
        temperature : float
            Температура генерации.
        max_continuation_attempts : int, optional
            Максимальное количество попыток продолжить генерацию, по умолчанию 3.
        continuation_prompt_template : str, optional
            Шаблон промпта для запроса продолжения.
            По умолчанию используется шаблон, просящий продолжить с места обрыва.

        Returns
        -------
        str
            Полный (насколько возможно) сгенерированный ответ.
        """
        pass
