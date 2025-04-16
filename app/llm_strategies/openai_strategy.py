"""
Реализация стратегии для взаимодействия с API OpenAI.
Наследуется от BaseChatModelStrategy и реализует специфические
для OpenAI методы и логику.
"""

from typing import List, Dict
from openai import OpenAI
from llm_strategies.base_chat_model_strategy import BaseChatModelStrategy
from llm_strategies.model import Model


class OpenAIChatStrategy(BaseChatModelStrategy):
    """
    Конкретная стратегия для взаимодействия с API OpenAI.

    Наследует общую функциональность от BaseChatModelStrategy и добавляет
    специфичную для OpenAI логику работы с API.

    Parameters
    ----------
    api_key : str
        API ключ для доступа к API OpenAI.
    """

    def __init__(self, api_key: str):
        """
        Инициализирует стратегию OpenAI и настраивает клиент API.

        Parameters
        ----------
        api_key : str
            API ключ для доступа к API OpenAI.
        """
        super().__init__(api_key)
        self.models = [
            Model(
                name="gpt-4.1",
                output_max_tokens=32_768,
                price_input=2.0,
                price_output=8.0,
            ),
            Model(
                name="gpt-4o",
                output_max_tokens=16_384,
                price_input=2.5,
                price_output=10.0,
            ),
            Model(
                name="gpt-4.1-mini",
                output_max_tokens=32_768,
                price_input=0.40,
                price_output=1.60,
            ),
            Model(
                name="gpt-4o-mini",
                output_max_tokens=16_384,
                price_input=0.15,
                price_output=0.6,
            ),
            Model(
                name="gpt-4.1-nano",
                output_max_tokens=32_768,
                price_input=0.10,
                price_output=0.40,
            ),
            Model(
                name="o3-mini",
                output_max_tokens=100_000,
                price_input=1.10,
                price_output=4.40,
            ),
            Model(
                name="o1",
                output_max_tokens=32_768,
                price_input=15.00,
                price_output=60.00,
            ),
            Model(
                name="o1-preview",
                output_max_tokens=32_768,
                price_input=15.00,
                price_output=60.00,
            ),
        ]
        self.client = OpenAI(api_key=self.api_key)
        self.reasoning_tokens = 0

    def get_full_price(self) -> float:
        """
        Рассчитывает и возвращает полную стоимость запроса по ценам OpenAI.

        Переопределяет базовый метод для учета специфики ценообразования OpenAI:
        - Токены записи в кэш стоят столько же как входные токены
        - Токены чтения из кэша на 50% дешевле базовых входных токенов

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

        # Токены записи в кэш стоят столько же как входные токены
        cache_create = self.cache_create_tokens * model_info.price_input / 1_000_000.0

        # Токены чтения из кэша на 50% дешевле базовых входных токенов
        cache_read = self.cache_read_tokens * model_info.price_input * 0.5 / 1_000_000.0

        return inputs + outputs + cache_create + cache_read

    def send_message(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model_name: str,
        max_tokens: int,
        temperature: float = 0,
    ) -> str:
        """
        Отправляет сообщение в API OpenAI и возвращает сгенерированный ответ.

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
            Сгенерированный ответ от API OpenAI.
        """
        self.model = model_name

        if system_prompt:
            full_messages = [{"role": "developer", "content": f"{system_prompt}"}]
        else:
            full_messages = []
        full_messages.extend(messages)

        if model_name in ["o1-mini", "o3-mini", "o1"]:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=full_messages,
                max_completion_tokens=max_tokens,
            )
        else:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

        self.output_tokens = response.usage.completion_tokens
        self.cache_create_tokens = 0
        self.cache_read_tokens = response.usage.prompt_tokens_details.cached_tokens
        self.input_tokens = response.usage.prompt_tokens - self.cache_read_tokens

        return response.choices[0].message.content
