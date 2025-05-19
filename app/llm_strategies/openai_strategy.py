"""
Реализация стратегии для взаимодействия с API OpenAI.
Наследуется от BaseChatModelStrategy и реализует специфические
для OpenAI методы и логику.
"""

from typing import List, Dict, Tuple, Optional
from openai import OpenAI
from llm_strategies.base_chat_model_strategy import BaseChatModelStrategy
from llm_strategies.model import Model
from utils.logger import log_warning


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
                name="o3",
                output_max_tokens=100_000,
                price_input=10.0,
                price_output=40.0,
            ),
            Model(
                name="o4-mini",
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
    ) -> Tuple[str, Optional[str]]:
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
        Tuple[str, Optional[str]]
            Кортеж: (сгенерированный ответ от API OpenAI модели, причина завершения генерации).
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

        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason

        self.output_tokens = response.usage.completion_tokens
        self.cache_create_tokens = 0
        self.cache_read_tokens = response.usage.prompt_tokens_details.cached_tokens
        self.input_tokens = response.usage.prompt_tokens - self.cache_read_tokens

        return content, finish_reason

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
        self.model = model_name

        full_response_content = ""
        # current_messages будет хранить историю диалога для API
        # не включая системный промпт, так как send_message его обрабатывает отдельно
        current_messages: List[Dict[str, str]] = []

        # Сброс и агрегация токенов
        aggregated_input_tokens = 0
        aggregated_output_tokens = 0
        aggregated_cache_create_tokens = 0
        aggregated_cache_read_tokens = 0

        # Первое сообщение пользователя
        current_messages.append({"role": "user", "content": initial_user_message})

        for attempt in range(max_continuation_attempts):
            # Вызываем send_message текущей стратегии.
            # Передаем копию current_messages, чтобы send_message не модифицировал его случайно
            chunk_content, finish_reason = self.send_message(
                system_prompt=system_prompt,
                messages=list(current_messages),  # Передаем текущую историю
                model_name=model_name,
                max_tokens=max_tokens_per_chunk,
                temperature=temperature,
            )

            # Агрегируем токены ПОСЛЕ вызова send_message,
            # т.к. send_message обновляет self.input_tokens и т.д. для *этого конкретного* вызова.
            aggregated_input_tokens += self.get_input_tokens()
            aggregated_output_tokens += self.get_output_tokens()
            aggregated_cache_create_tokens += self.get_cache_create_tokens()
            aggregated_cache_read_tokens += self.get_cache_read_tokens()

            if chunk_content:
                full_response_content += chunk_content

            is_last_attempt = attempt == max_continuation_attempts - 1

            # Проверяем причину завершения конкретно для OpenAI API
            truncated_by_length = finish_reason == "length"

            if truncated_by_length and not is_last_attempt:
                # Добавляем ответ ассистента в историю
                current_messages.append(
                    {"role": "assistant", "content": chunk_content or ""}
                )  # chunk_content может быть None
                # Формируем и добавляем новый user-промпт для продолжения
                continuation_user_message_content = continuation_prompt_template.format(
                    previous_content=chunk_content or ""
                )
                current_messages.append(
                    {"role": "user", "content": continuation_user_message_content}
                )
            else:
                if truncated_by_length and is_last_attempt:
                    log_warning(
                        f"Response still truncated after {max_continuation_attempts} attempts."
                    )
                break  # Выход из цикла, если ответ полный или исчерпаны попытки

        # Обновляем общие токены агрегированными значениями
        # чтобы get_input_tokens() и т.д. после вызова generate_full_response
        # возвращали суммарные значения за всю операцию.
        self.input_tokens = aggregated_input_tokens
        self.output_tokens = aggregated_output_tokens
        self.cache_create_tokens = aggregated_cache_create_tokens
        self.cache_read_tokens = aggregated_cache_read_tokens

        return full_response_content.strip()
