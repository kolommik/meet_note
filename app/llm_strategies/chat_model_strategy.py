"""
This module implements the Strategy pattern for interacting with different chat model APIs.

Defines the ChatModelStrategy abstract base class, which serves as the common interface for all chat model strategies.
This class enforces the implementation of essential methods for interacting with chat model APIs.

Guidelines for refactoring and extending this module:
1. Adhere to the Strategy pattern
2. Avoid coupling the strategies with the client code
3. Keep the strategies focused and cohesive
4. Consider extracting common functionality
5. Maintain the interface of `ChatModelStrategy`

Following these guidelines will keep the module flexible, extensible, and aligned with the Strategy pattern.
"""

from typing import List, Dict
from abc import ABC, abstractmethod


class ChatModelStrategy(ABC):
    """
    Abstract base class for chat model strategies.

    This class defines the common interface for all chat model strategies and enforces the implementation
    of essential methods for interacting with chat model APIs.

    Methods
    -------
    get_models()
        Returns a list of available models for a strategy.
    get_output_max_tokens(model_name)
        Returns the maximum number of output tokens for the specified model.
    get_input_tokens()
        Returns the number of input tokens used in the last API request.
    get_output_tokens()
        Returns the number of output tokens generated in the last API response.
    get_full_price()
        Calculates and returns the total price based on the input and output tokens.
    send_message(system_prompt, messages, model_name, max_tokens, temperature)
        Sends a message to the chat model API and returns the generated response.
    """

    @abstractmethod
    def get_models(self) -> List[str]:
        """
        Returns a list of available models for a strategy.

        Returns
        -------
        List[str]
            A list of available model names.
        """
        pass

    @abstractmethod
    def get_output_max_tokens(self, model_name: str) -> int:
        """
        Returns the maximum number of output tokens for the specified model.

        Parameters
        ----------
        model_name : str
            The name of the model.

        Returns
        -------
        int
            The maximum number of output tokens for the specified model.
        """
        pass

    @abstractmethod
    def get_input_tokens(self) -> int:
        """
        Returns the number of input tokens used in the last API request.

        Returns
        -------
        int
            The number of input tokens used in the last API request.
        """
        pass

    @abstractmethod
    def get_output_tokens(self) -> int:
        """
        Returns the number of output tokens generated in the last API response.

        Returns
        -------
        int
            The number of output tokens generated in the last API response.
        """
        pass

    @abstractmethod
    def get_cache_create_tokens(self) -> int:
        """
        Returns the number of cashed input tokens used in the last API request.

        Returns
        -------
        int
            The number of cashed input tokens generated in the last API response.
        """
        pass

    @abstractmethod
    def get_cache_read_tokens(self) -> int:
        """
        Returns the number of used cashed tokens used in the last API request.

        Returns
        -------
        int
            The number of used cashed tokens generated in the last API response.
        """
        pass

    @abstractmethod
    def get_full_price(self) -> float:
        """
        Calculates and returns the total price based on the input and output tokens.

        Returns
        -------
        float
            The total price based on the input and output tokens.
        """
        pass

    @abstractmethod
    def send_message(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model_name: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """
        Sends a message to the chat model API and returns the generated response.

        Parameters
        ----------
        system_prompt : str
            The system prompt to provide context for the conversation.
        messages : List[Dict[str, str]]
            A list of messages in the conversation, each represented as a dictionary.
        model_name : str
            The name of the model to use for generating the response.
        max_tokens : int
            The maximum number of tokens to generate in the response.
        temperature : float
            The temperature value to control the randomness of the generated response.

        Returns
        -------
        str
            The generated response from the chat model API.
        """
        pass
