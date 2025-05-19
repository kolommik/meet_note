"""
Модуль реализует паттерн Стратегия для взаимодействия с разными API чат-моделей.

Определяет абстрактный базовый класс ChatModelStrategy, который служит
общим интерфейсом для всех стратегий чат-моделей. Этот класс требует
реализации основных методов для взаимодействия с API чат-моделей.

Рекомендации по рефакторингу и расширению этого модуля:
1. Следуйте паттерну Стратегия
2. Избегайте связывания стратегий с клиентским кодом
3. Поддерживайте стратегии сфокусированными и связными
4. Рассмотрите возможность извлечения общей функциональности в базовый класс
5. Сохраняйте интерфейс `ChatModelStrategy`

Следование этим рекомендациям сохранит модуль гибким, расширяемым и соответствующим
паттерну Стратегия.
"""

from typing import List, Dict, Tuple, Optional
from abc import ABC, abstractmethod


class ChatModelStrategy(ABC):
    """
    Абстрактный базовый класс для стратегий чат-моделей.

    Этот класс определяет общий интерфейс для всех стратегий чат-моделей
    и требует реализации основных методов для взаимодействия с API чат-моделей.

    Methods
    -------
    get_models()
        Возвращает список доступных моделей для стратегии.
    get_output_max_tokens(model_name)
        Возвращает максимальное количество выходных токенов для указанной модели.
    get_input_tokens()
        Возвращает количество входных токенов, использованных в последнем API-запросе.
    get_output_tokens()
        Возвращает количество выходных токенов, сгенерированных в последнем API-ответе.
    get_cache_create_tokens()
        Возвращает количество токенов, используемых для создания кэша.
    get_cache_read_tokens()
        Возвращает количество токенов, прочитанных из кэша.
    get_full_price()
        Рассчитывает и возвращает полную стоимость на основе входных и выходных токенов.
    send_message(system_prompt, messages, model_name, max_tokens, temperature)
        Отправляет одиночное сообщение к API чат-модели и возвращает ответ и причину завершения.
    generate_full_response(system_prompt, initial_user_message, model_name, max_tokens_per_chunk, temperature, ...)
        Отправляет сообщение и автоматически обрабатывает продолжения для получения полного ответа.
    """

    @abstractmethod
    def get_models(self) -> List[str]:
        """
        Возвращает список доступных моделей для стратегии.

        Returns
        -------
        List[str]
            Список названий доступных моделей.
        """
        pass

    @abstractmethod
    def get_output_max_tokens(self, model_name: str) -> int:
        """
        Возвращает максимальное количество выходных токенов для указанной модели.

        Parameters
        ----------
        model_name : str
            Название модели.

        Returns
        -------
        int
            Максимальное количество выходных токенов для указанной модели.
        """
        pass

    @abstractmethod
    def get_input_tokens(self) -> int:
        """
        Возвращает количество входных токенов, использованных в последнем API-запросе
        (или сумму токенов, если использовался generate_full_response).

        Returns
        -------
        int
            Количество входных токенов.
        """
        pass

    @abstractmethod
    def get_output_tokens(self) -> int:
        """
        Возвращает количество выходных токенов, сгенерированных в последнем API-ответе
        (или сумму токенов, если использовался generate_full_response).

        Returns
        -------
        int
            Количество выходных токенов.
        """
        pass

    @abstractmethod
    def get_cache_create_tokens(self) -> int:
        """
        Возвращает количество токенов, используемых для создания кэша.
        (или сумму токенов, если использовался generate_full_response).


        Returns
        -------
        int
            Количество токенов создания кэша.
        """
        pass

    @abstractmethod
    def get_cache_read_tokens(self) -> int:
        """
        Возвращает количество токенов, прочитанных из кэша.
        (или сумму токенов, если использовался generate_full_response).

        Returns
        -------
        int
            Количество токенов чтения из кэша.
        """
        pass

    @abstractmethod
    def get_full_price(self) -> float:
        """
        Рассчитывает и возвращает полную стоимость на основе входных и выходных токенов.

        Returns
        -------
        float
            Полная стоимость запроса в долларах США.
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
    ) -> Tuple[str, Optional[str]]:
        """
        Отправляет одиночное сообщение к API чат-модели и возвращает сгенерированный ответ
        и причину завершения генерации.

        Parameters
        ----------
        system_prompt : str
            Системный промпт для контекста разговора.
        messages : List[Dict[str, str]]
            Список сообщений в разговоре (только user/assistant).
        model_name : str
            Название модели для генерации ответа.
        max_tokens : int
            Максимальное количество токенов для генерации в ответе.
        temperature : float
            Температура генерации для контроля случайности сгенерированного ответа.

        Returns
        -------
        Tuple[str, Optional[str]]
            Кортеж: (сгенерированный ответ от API чат-модели, причина завершения генерации).
        """
        pass

    @abstractmethod
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
        pass
