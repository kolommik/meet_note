import logging
import os

# Создаем директорию для логов, если она не существует
os.makedirs("./logs", exist_ok=True)

# Глобальная переменная для отслеживания инициализации логгера
logger = None


def setup_logger():
    """
    Настройка логгера с предотвращением дублирования обработчиков
    """
    global logger

    # Если логгер уже настроен, просто возвращаем его
    if logger is not None:
        return logger

    # Создаем или получаем существующий логгер
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.INFO)

    # Проверяем, есть ли уже обработчики
    if not logger.handlers:
        # Создаем обработчик файла
        log_file = os.path.join("./logs", "app.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")

        # Формат сообщения
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Добавляем обработчик к логгеру
        logger.addHandler(file_handler)

    return logger


# Инициализация логгера при импорте модуля
logger = setup_logger()


def log_info(message):
    """Записать информационное сообщение в лог"""
    logger.info(message)


def log_error(message):
    """Записать сообщение об ошибке в лог"""
    logger.error(message)


def log_file_upload(filename, size):
    """Логирование загрузки файла"""
    logger.info(f"File uploaded: {filename}, Size: {size} bytes")


def get_logs():
    """Получить содержимое файла логов"""
    try:
        log_file = os.path.join("./logs", "app.log")
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                return f.read()
        return "Log file not found"
    except Exception as e:
        return f"Error reading log file: {str(e)}"
