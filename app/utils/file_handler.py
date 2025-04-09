import os
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
