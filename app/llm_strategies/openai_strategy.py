"""
Implements the OpenAIChatStrategy, a concrete strategy for interacting with the OpenAI chat model API.
This strategy adheres to the ChatModelStrategy interface and encapsulates OpenAI-specific functionality.
"""

from typing import List, Dict
from openai import OpenAI
from llm_strategies.model import Model
from llm_strategies.chat_model_strategy import ChatModelStrategy


# https://platform.openai.com/docs/models
# https://openai.com/api/pricing/
class OpenAIChatStrategy(ChatModelStrategy):
    """
    A concrete strategy for interacting with the OpenAI chat model API.

    Parameters
    ----------
    api_key : str
        The API key for accessing the OpenAI API.

    Attributes
    ----------
    api_key : str
        The API key for accessing the OpenAI API.
    models : List[Model]
        A list of available OpenAI models.
    client : OpenAI
        The OpenAI client instance for making API requests.
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
        Sends a message to the OpenAI API and returns the generated response.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
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
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_create_tokens = 0
        self.cache_read_tokens = 0
        self.reasoning_tokens = 0
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
        # Токены записи в кэш стоят столько же как входные токены
        cache_create = (
            self.cache_create_tokens
            * self.models[self.get_models().index(self.model)].price_input
            / 1_000_000.0
        )
        # Токены чтения из кэша на 50% дешевле базовых входных токенов
        cache_read = (
            self.cache_read_tokens
            * self.models[self.get_models().index(self.model)].price_input
            * 0.5
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
