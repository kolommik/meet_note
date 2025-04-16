"""
Реализация стратегии для взаимодействия с API Anthropic.
Наследуется от BaseChatModelStrategy и реализует специфические
для Anthropic методы и логику.
"""

from typing import List, Dict
from anthropic import Anthropic
from llm_strategies.base_chat_model_strategy import BaseChatModelStrategy
from llm_strategies.model import Model


class AnthropicChatStrategy(BaseChatModelStrategy):
    """
    Конкретная стратегия для взаимодействия с API Anthropic.

    Наследует общую функциональность от BaseChatModelStrategy и добавляет
    специфичную для Anthropic логику работы с API.

    Parameters
    ----------
    api_key : str
        API ключ для доступа к API Anthropic.
    """

    def __init__(self, api_key: str):
        """
        Инициализирует стратегию Anthropic и настраивает клиент API.

        Parameters
        ----------
        api_key : str
            API ключ для доступа к API Anthropic.
        """
        super().__init__(api_key)
        self.models = [
            Model(
                name="claude-3-7-sonnet-latest",
                output_max_tokens=8192,
                price_input=3.0,
                price_output=15.0,
            ),
            Model(
                name="claude-3-5-sonnet-latest",
                output_max_tokens=8192,
                price_input=3.0,
                price_output=15.0,
            ),
            Model(
                name="claude-3-5-haiku-latest",
                output_max_tokens=4096,
                price_input=0.8,
                price_output=4.0,
            ),
            Model(
                name="claude-3-5-sonnet-20240620",
                output_max_tokens=8192,
                price_input=3.0,
                price_output=15.0,
            ),
            Model(
                name="claude-3-opus-latest",
                output_max_tokens=4096,
                price_input=15.0,
                price_output=75.0,
            ),
            Model(
                name="claude-3-haiku-20240307",
                output_max_tokens=4096,
                price_input=0.25,
                price_output=1.25,
            ),
        ]
        self.client = Anthropic(api_key=self.api_key)

    def get_full_price(self) -> float:
        """
        Рассчитывает и возвращает полную стоимость запроса по ценам Anthropic.

        Переопределяет базовый метод для учета специфики ценообразования Anthropic:
        - Токены записи в кэш на 25% дороже базовых входных токенов
        - Токены чтения из кэша на 90% дешевле базовых входных токенов

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

        # Токены записи в кэш на 25% дороже базовых входных токенов
        cache_create = (
            self.cache_create_tokens * model_info.price_input * 1.25 / 1_000_000.0
        )

        # Токены чтения из кэша на 90% дешевле базовых входных токенов
        cache_read = self.cache_read_tokens * model_info.price_input * 0.1 / 1_000_000.0

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
        Отправляет сообщение в API Anthropic и возвращает сгенерированный ответ.

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
            Сгенерированный ответ от API Anthropic.
        """
        self.model = model_name

        cashed_messages = []
        message_count = len(messages)
        used_cashed_control_breakpoints = 0
        for i, message in enumerate(messages):
            new_message = {
                "role": message["role"],
                "content": [
                    {
                        "type": "text",
                        "text": message["content"],
                    }
                ],
            }
            # Добавляем cache_control к 0 сообщению и последним 3м
            if (
                (i == 0 or i >= message_count - 6)
                and used_cashed_control_breakpoints < 4
                and message["role"] == "user"
            ):
                used_cashed_control_breakpoints += 1
                new_message["content"][0]["cache_control"] = {"type": "ephemeral"}
            cashed_messages.append(new_message)

        response = self.client.messages.create(
            model=model_name,
            system=system_prompt,
            messages=cashed_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
        )

        self.input_tokens = response.usage.input_tokens
        self.output_tokens = response.usage.output_tokens
        self.cache_create_tokens = response.usage.cache_creation_input_tokens
        self.cache_read_tokens = response.usage.cache_read_input_tokens

        return response.content[0].text
