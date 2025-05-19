"""
Реализация стратегии для взаимодействия с API Anthropic.
Наследуется от BaseChatModelStrategy и реализует специфические
для Anthropic методы и логику.
"""

from typing import List, Dict, Tuple, Optional
from anthropic import Anthropic
from llm_strategies.base_chat_model_strategy import BaseChatModelStrategy
from llm_strategies.model import Model
from utils.logger import log_warning


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
    ) -> Tuple[str, Optional[str]]:
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
        Tuple[str, Optional[str]]
            Кортеж: (сгенерированный ответ от API Anthropic, причина завершения генерации).
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

        content = response.content[0].text
        finish_reason = response.stop_reason

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

            aggregated_input_tokens += self.get_input_tokens()
            aggregated_output_tokens += self.get_output_tokens()
            aggregated_cache_create_tokens += self.get_cache_create_tokens()
            aggregated_cache_read_tokens += self.get_cache_read_tokens()

            if chunk_content:
                full_response_content += chunk_content

            is_last_attempt = attempt == max_continuation_attempts - 1

            # Проверяем причину завершения конкретно для Anthropic API
            truncated_by_length = finish_reason == "max_tokens"

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
