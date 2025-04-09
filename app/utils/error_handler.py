from enum import Enum
import traceback
from typing import Any, Optional, Callable, TypeVar
import streamlit as st
from utils.logger import log_error, log_info

# Тип для возвращаемого значения функции
T = TypeVar("T")


class ErrorType(Enum):
    """Типы ошибок приложения."""

    FILE_ERROR = "Ошибка при работе с файлом"
    API_ERROR = "Ошибка при обращении к API"
    TRANSCRIPTION_ERROR = "Ошибка при распознавании речи"
    LLM_ERROR = "Ошибка при анализе с помощью LLM"
    CONFIG_ERROR = "Ошибка в конфигурации"
    UNKNOWN_ERROR = "Неизвестная ошибка"


def handle_error(
    error_type: ErrorType,
    exception: Exception,
    show_ui_error: bool = True,
    default_return: Optional[Any] = None,
) -> Any:
    """
    Централизованная обработка ошибок с логированием и отображением в UI.

    Args:
        error_type: Тип ошибки из перечисления ErrorType
        exception: Объект исключения
        show_ui_error: Нужно ли отображать ошибку в UI (через st.error)
        default_return: Значение, возвращаемое при ошибке

    Returns:
        default_return или None
    """
    error_msg = f"{error_type.value}: {str(exception)}"

    # Подробное логирование
    log_error(error_msg)
    log_error(traceback.format_exc())

    # Отображение в UI при необходимости
    if show_ui_error:
        st.error(error_msg)

    return default_return


def safe_operation(
    operation: Callable[..., T],
    error_type: ErrorType,
    show_ui_error: bool = True,
    default_return: Optional[T] = None,
    operation_name: Optional[str] = None,
    *args,
    **kwargs,
) -> T:
    """
    Декоратор для безопасного выполнения операций с единообразной обработкой ошибок.

    Args:
        operation: Функция для выполнения
        error_type: Тип ошибки из перечисления ErrorType
        show_ui_error: Нужно ли отображать ошибку в UI
        default_return: Значение по умолчанию при ошибке
        operation_name: Имя операции для логирования (если None, будет использовано имя функции)
        *args, **kwargs: Аргументы для передачи в функцию

    Returns:
        Результат функции или default_return при ошибке
    """
    if operation_name is None:
        operation_name = operation.__name__

    try:
        log_info(f"Начало выполнения операции: {operation_name}")
        result = operation(*args, **kwargs)
        log_info(f"Операция {operation_name} успешно выполнена")
        return result
    except Exception as e:
        return handle_error(error_type, e, show_ui_error, default_return)
