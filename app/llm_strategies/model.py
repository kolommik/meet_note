"""
Defines the Model class, which represents a chat model with its associated properties such as name, output_max_tokens,
price_input, and price_output.
This class is used by the chat model strategies to store and access model-specific information.
"""


class Model:
    """
    Represents a chat model with its associated properties.

    Parameters
    ----------
    name : str
        The name of the model.
    output_max_tokens : int
        The maximum number of output tokens the model can generate.
    price_input : float
        The price per input token for the model.
    price_output : float
        The price per output token for the model.

    Attributes
    ----------
    name : str
        The name of the model.
    output_max_tokens : int
        The maximum number of output tokens the model can generate.
    price_input : float
        The price per input token for the model.
    price_output : float
        The price per output token for the model.
    """

    def __init__(
        self, name: str, output_max_tokens: int, price_input: float, price_output: float
    ):
        self.name = name
        self.output_max_tokens = output_max_tokens
        self.price_input = price_input
        self.price_output = price_output
