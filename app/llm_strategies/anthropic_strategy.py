"""
Implements the AnthropicChatStrategy, a concrete strategy for interacting with the Anthropic chat model API.
This strategy adheres to the ChatModelStrategy interface and encapsulates Anthropic-specific functionality.
"""

from typing import List, Dict
from anthropic import Anthropic
from llm_strategies.chat_model_strategy import ChatModelStrategy
from llm_strategies.model import Model


# https://docs.anthropic.com/en/docs/about-claude/models/all-models
class AnthropicChatStrategy(ChatModelStrategy):
    """
    A concrete strategy for interacting with the Anthropic chat model API.

    Parameters
    ----------
    api_key : str
        The API key for accessing the Anthropic API.

    Attributes
    ----------
    api_key : str
        The API key for accessing the Anthropic API.
    models : List[Model]
        A list of available Anthropic models.
    client : Anthropic
        The Anthropic client instance for making API requests.
    input_tokens : int
        The number of input tokens used in the last API request.
    output_tokens : int
        The number of output tokens generated in the last API response.
    model : str
        The name of the model used in the last API request.

    Methods
    -------
    get_models()
        Returns a list of available model names.
    get_output_max_tokens(model_name)
        Returns the maximum number of output tokens for the specified model.
    get_input_tokens()
        Returns the number of input tokens used in the last API request.
    get_output_tokens()
        Returns the number of output tokens generated in the last API response.
    get_full_price()
        Calculates and returns the total price based on the input and output tokens.
    send_message(system_prompt, messages, model_name, max_tokens, temperature)
        Sends a message to the Anthropic API and returns the generated response.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
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
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_create_tokens = 0
        self.cache_read_tokens = 0
        self.model = None

    def get_models(self) -> List[str]:
        return [model.name for model in self.models]

    def get_output_max_tokens(self, model_name: str) -> int:
        return self.models[self.get_models().index(model_name)].output_max_tokens

    def get_input_tokens(self) -> int:
        return self.input_tokens

    def get_output_tokens(self) -> int:
        return self.output_tokens

    def get_cache_create_tokens(self) -> int:
        return self.cache_create_tokens

    def get_cache_read_tokens(self) -> int:
        return self.cache_read_tokens

    def get_full_price(self) -> float:
        # Проверяем, инициализирована ли модель
        if self.model is None:
            return 0.0  # Возвращаем 0, если модель не определена

        inputs = (
            self.input_tokens
            * self.models[self.get_models().index(self.model)].price_input
            / 1_000_000.0
        )
        outputs = (
            self.output_tokens
            * self.models[self.get_models().index(self.model)].price_output
            / 1_000_000.0
        )
        # Токены записи в кэш на 25% дороже базовых входных токенов
        cache_create = (
            self.cache_create_tokens
            * self.models[self.get_models().index(self.model)].price_input
            * 1.25
            / 1_000_000.0
        )
        # Токены чтения из кэша на 90% дешевле базовых входных токенов
        cache_read = (
            self.cache_read_tokens
            * self.models[self.get_models().index(self.model)].price_input
            * 0.1
            / 1_000_000.0
        )

        return inputs + outputs + cache_create + cache_read

    def send_message(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model_name: str,
        max_tokens: int,
        temperature: float = 0,
    ) -> str:

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
