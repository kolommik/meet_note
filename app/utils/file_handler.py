import os
from typing import Optional
from utils.logger import log_file_upload
from utils.error_handler import ErrorType, safe_operation
from utils.config import get_config


def save_uploaded_file(uploaded_file):
    """
    Сохранение загруженного файла в папку data

    Args:
        uploaded_file: Объект загруженного файла из st.file_uploader

    Returns:
        tuple: (путь к сохраненному файлу, размер файла в байтах)
    """
    return safe_operation(
        _save_uploaded_file_impl,
        ErrorType.FILE_ERROR,
        operation_name="Сохранение загруженного файла",
        uploaded_file=uploaded_file,
        default_return=(None, 0),
    )


def _save_uploaded_file_impl(uploaded_file):
    """
    Внутренняя реализация для сохранения загруженного файла

    Args:
        uploaded_file: Объект загруженного файла из st.file_uploader

    Returns:
        tuple: (путь к сохраненному файлу, размер файла в байтах)
    """
    # Получаем полный путь для сохранения файла
    config = get_config()
    file_path = os.path.join(config.data_dir, uploaded_file.name)

    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Получаем размер файла
    file_size = os.path.getsize(file_path)

    # Логируем загрузку файла
    log_file_upload(uploaded_file.name, file_size)

    return file_path, file_size


def format_size(size_bytes):
    """
    Форматирование размера файла в читаемый вид

    Args:
        size_bytes: Размер в байтах

    Returns:
        str: Отформатированный размер (например, "1.23 MB")
    """
    return safe_operation(
        _format_size_impl,
        ErrorType.UNKNOWN_ERROR,
        size_bytes=size_bytes,
        default_return=f"{size_bytes} B",
    )


def _format_size_impl(size_bytes):
    """
    Внутренняя реализация форматирования размера файла

    Args:
        size_bytes: Размер в байтах

    Returns:
        str: Отформатированный размер (например, "1.23 MB")
    """
    # Определяем единицы измерения
    units = ["B", "KB", "MB", "GB", "TB"]

    # Находим подходящую единицу
    unit_index = 0
    size_value = float(size_bytes)

    while size_value >= 1024 and unit_index < len(units) - 1:
        size_value /= 1024
        unit_index += 1

    # Форматируем результат
    return f"{size_value:.2f} {units[unit_index]}"


def save_markdown_document(
    content: str, filename: str, directory: Optional[str] = None
) -> str:
    """
    Сохраняет Markdown-документ в указанную директорию.

    Args:
        content: Содержимое документа
        filename: Имя файла без расширения
        directory: Директория для сохранения (по умолчанию используется data_dir)

    Returns:
        str: Полный путь к сохраненному файлу
    """
    return safe_operation(
        _save_markdown_document_impl,
        ErrorType.FILE_ERROR,
        operation_name="Сохранение Markdown-документа",
        content=content,
        filename=filename,
        directory=directory,
        default_return=None,
    )


def _save_markdown_document_impl(
    content: str, filename: str, directory: Optional[str] = None
) -> str:
    """
    Внутренняя реализация для сохранения Markdown-документа

    Args:
        content: Содержимое документа
        filename: Имя файла без расширения
        directory: Директория для сохранения (по умолчанию используется data_dir)

    Returns:
        str: Полный путь к сохраненному файлу
    """
    # Если директория не указана, используем директорию данных из конфигурации
    if directory is None:
        config = get_config()
        directory = config.data_dir

    # Убедимся, что у файла есть расширение .md
    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    # Получаем полный путь для сохранения файла
    file_path = os.path.join(directory, filename)

    # Сохраняем файл
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


def read_markdown_document(file_path: str) -> Optional[str]:
    """
    Читает содержимое Markdown-документа из указанного пути.

    Args:
        file_path: Путь к файлу

    Returns:
        Optional[str]: Содержимое файла или None в случае ошибки
    """
    return safe_operation(
        _read_markdown_document_impl,
        ErrorType.FILE_ERROR,
        operation_name="Чтение Markdown-документа",
        file_path=file_path,
        default_return=None,
    )


def _read_markdown_document_impl(file_path: str) -> str:
    """
    Внутренняя реализация для чтения Markdown-документа

    Args:
        file_path: Путь к файлу

    Returns:
        str: Содержимое файла
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def get_document_path(filename: str, directory: Optional[str] = None) -> str:
    """
    Получает полный путь к документу в указанной директории.

    Args:
        filename: Имя файла
        directory: Директория (по умолчанию используется data_dir)

    Returns:
        str: Полный путь к файлу
    """
    if directory is None:
        config = get_config()
        directory = config.data_dir

    # Убедимся, что у файла есть расширение .md
    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    return os.path.join(directory, filename)
