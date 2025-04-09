import os
import streamlit as st
from utils.logger import log_file_upload

# Создаем директорию для данных, если она не существует
os.makedirs("./data", exist_ok=True)


def save_uploaded_file(uploaded_file):
    """
    Сохранение загруженного файла в папку data

    Args:
        uploaded_file: Объект загруженного файла из st.file_uploader

    Returns:
        tuple: (путь к сохраненному файлу, размер файла в байтах)
    """
    try:
        # Получаем полный путь для сохранения файла
        file_path = os.path.join("./data", uploaded_file.name)

        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Получаем размер файла
        file_size = os.path.getsize(file_path)

        # Логируем загрузку файла
        log_file_upload(uploaded_file.name, file_size)

        return file_path, file_size
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None, 0


def format_size(size_bytes):
    """
    Форматирование размера файла в читаемый вид

    Args:
        size_bytes: Размер в байтах

    Returns:
        str: Отформатированный размер (например, "1.23 MB")
    """
    # Определяем единицы измерения
    units = ["B", "KB", "MB", "GB", "TB"]

    # Находим подходящую единицу
    unit_index = 0
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1

    # Форматируем результат
    return f"{size_bytes:.2f} {units[unit_index]}"
