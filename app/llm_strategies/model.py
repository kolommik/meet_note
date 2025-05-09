"""
Определяет класс Model, который представляет чат-модель с соответствующими свойствами,
такими как name (название), output_max_tokens (максимальное количество выходных токенов),
price_input (цена входных токенов) и price_output (цена выходных токенов).
Этот класс используется стратегиями чат-моделей для хранения и доступа
к специфичной для модели информации.
"""


class Model:
    """
    Представляет чат-модель с соответствующими свойствами.

    Parameters
    ----------
    name : str
        Название модели.
    output_max_tokens : int
        Максимальное количество выходных токенов, которые может сгенерировать модель.
    price_input : float
        Цена за входной токен для модели (в долларах США за 1 миллион токенов).
    price_output : float
        Цена за выходной токен для модели (в долларах США за 1 миллион токенов).

    Attributes
    ----------
    name : str
        Название модели.
    output_max_tokens : int
        Максимальное количество выходных токенов, которые может сгенерировать модель.
    price_input : float
        Цена за входной токен для модели (в долларах США за 1 миллион токенов).
    price_output : float
        Цена за выходной токен для модели (в долларах США за 1 миллион токенов).
    """

    def __init__(
        self, name: str, output_max_tokens: int, price_input: float, price_output: float
    ):
        self.name = name
        self.output_max_tokens = output_max_tokens
        self.price_input = price_input
        self.price_output = price_output
