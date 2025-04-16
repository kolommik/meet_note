"""
Реализация стратегии для взаимодействия с API Deepseek.
Наследуется от BaseChatModelStrategy и реализует специфические
для Deepseek методы и логику.
"""

from typing import List, Dict
from openai import OpenAI
from llm_strategies.base_chat_model_strategy import BaseChatModelStrategy
from llm_strategies.model import Model


class DeepseekChatStrategy(BaseChatModelStrategy):
    """
    Конкретная стратегия для взаимодействия с API Deepseek.

    Наследует общую функциональность от BaseChatModelStrategy и добавляет
    специфичную для Deepseek логику работы с API.

    Parameters
    ----------
    api_key : str
        API ключ для доступа к API Deepseek.
    """

    def __init__(self, api_key: str):
        """
        Инициализирует стратегию Deepseek и настраивает клиент API.

        Parameters
        ----------
        api_key : str
            API ключ для доступа к API Deepseek.
        """
        super().__init__(api_key)
        self.models = [
            # DeepSeek-V3 (обычная чат-модель)
            Model(
                name="deepseek-chat",
                output_max_tokens=4096,
                price_input=0.14,
                price_output=0.28,
            ),
            # DeepSeek-R1 (модель для рассуждений)
            Model(
                name="deepseek-reasoner",
                output_max_tokens=4096,
                price_input=0.55,  # Стоимость для cache miss
                price_output=2.19,
            ),
        ]
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

    def get_full_price(self) -> float:
        """
        Рассчитывает и возвращает полную стоимость запроса по ценам Deepseek.

        Переопределяет базовый метод для учета специфики ценообразования Deepseek:
        - Разные модели имеют разную стоимость
        - Особая обработка cached токенов
        - Для модели deepseek-reasoner учитывается выходной текст рассуждений и ответа

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

        # Базовая стоимость входных токенов (не из кэша)
        inputs = self.input_tokens * model_info.price_input / 1_000_000.0

        # Базовая стоимость выходных токенов
        outputs = self.output_tokens * model_info.price_output / 1_000_000.0

        # Токены записи в кэш стоят столько же как входные токены (cache miss)
        cache_create = self.cache_create_tokens * model_info.price_input / 1_000_000.0

        # Токены чтения из кэша (cache hit)
        # Для deepseek-reasoner цена cache hit = $0.14 / млн токенов
        # Для deepseek-chat используем базовую логику со скидкой 90%
        cache_read_price = (
            0.14 if self.model == "deepseek-reasoner" else model_info.price_input * 0.1
        )
        cache_read = self.cache_read_tokens * cache_read_price / 1_000_000.0

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
        Отправляет сообщение в API Deepseek и возвращает сгенерированный ответ.

        Parameters
        ----------
        system_prompt : str
            Системный промпт для контекста разговора.
        messages : List[Dict[str, str]]
            Список сообщений в разговоре, каждое представлено в виде словаря.
        model_name : str
            Название модели для генерации ответа (deepseek-chat или deepseek-reasoner).
        max_tokens : int
            Максимальное количество токенов для генерации в ответе.
        temperature : float, optional
            Температура генерации (случайность ответа), по умолчанию 0.

        Returns
        -------
        str
            Сгенерированный ответ от API Deepseek.
        """
        self.model = model_name

        full_messages = [{"role": "system", "content": f"{system_prompt}"}]
        full_messages.extend(messages)

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
        self.cache_create_tokens = response.usage.prompt_cache_miss_tokens
        self.cache_read_tokens = response.usage.prompt_cache_hit_tokens
        self.input_tokens = (
            response.usage.prompt_tokens
            - self.cache_create_tokens
            - self.cache_read_tokens
        )

        return response.choices[0].message.content
