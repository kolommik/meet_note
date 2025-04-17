import os
import requests
import json
from utils.logger import log_info
from utils.error_handler import safe_operation, ErrorType
from utils.config import get_config

# URL для API распознавания речи
STT_API_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def generate_human_readable_transcript(transcript_data):
    """
    Генерирует упрощенную человекочитаемую версию транскрипции
    с сохранением хронологического порядка говорящих, но без времени и языка

    Args:
        transcript_data: Данные распознавания от API

    Returns:
        str: Упрощенный текст транскрипции для отображения
    """
    return safe_operation(
        _generate_human_readable_transcript_impl,
        ErrorType.TRANSCRIPTION_ERROR,
        transcript_data=transcript_data,
        default_return="Не удалось сформировать читаемую транскрипцию.",
    )


def _generate_human_readable_transcript_impl(transcript_data):
    """
    Внутренняя реализация для генерации человекочитаемой версии транскрипции

    Args:
        transcript_data: Данные распознавания от API

    Returns:
        str: Упрощенный текст транскрипции для отображения
    """
    lines = []

    # Если нет информации о словах, возвращаем только общий текст
    if "words" not in transcript_data:
        lines.append(transcript_data.get("text", "Text not recognized."))
        return "\n".join(lines)

    # Список аудио-событий (будут игнорироваться)
    audio_events = []

    # Текущая информация об отрезке речи
    current_speaker = None
    current_text = []

    # Обрабатываем последовательно слова из API
    for word_info in transcript_data.get("words", []):
        # Обрабатываем аудио-события
        if word_info.get("type") == "audio_event" or "audio_event" in word_info:
            event = word_info.get("audio_event", "") or word_info.get("text", "")
            audio_events.append(f"[{event}]")
            continue

        # Пропускаем пробелы типа "spacing"
        if word_info.get("type") == "spacing":
            continue

        # Для обычных слов
        speaker = word_info.get("speaker_id")
        word = word_info.get("text", "")

        # Если это первое слово или новый говорящий
        if current_speaker is None or current_speaker != speaker:
            # Сохраняем предыдущее высказывание, если оно было
            if current_speaker is not None and current_text:
                speaker_text = " ".join(current_text)
                lines.append(f"{current_speaker}: {speaker_text}")

            # Начинаем новое высказывание
            current_speaker = speaker
            current_text = [word]
        else:
            # Продолжаем текущее высказывание
            current_text.append(word)

    # Добавляем последнее высказывание
    if current_speaker is not None and current_text:
        speaker_text = " ".join(current_text)
        lines.append(f"{current_speaker}: {speaker_text}")

    return "\n".join(lines)


def transcribe_audio(file_path):
    """
    Отправляет аудиофайл в ElevenLabs API для распознавания речи

    Args:
        file_path: Путь к аудиофайлу для распознавания

    Returns:
        dict: Словарь с результатами распознавания или None в случае ошибки
    """
    return safe_operation(
        _transcribe_audio_impl,
        ErrorType.API_ERROR,
        file_path=file_path,
        default_return=None,
    )


def _transcribe_audio_impl(file_path):
    """
    Внутренняя реализация для отправки аудиофайла в API распознавания речи

    Args:
        file_path: Путь к аудиофайлу для распознавания

    Returns:
        dict: Словарь с результатами распознавания
    """
    # Получаем конфигурацию
    config = get_config()

    if not config.elevenlabs_api_key:
        raise ValueError("API ключ ElevenLabs не найден в конфигурации")

    log_info(f"Начало распознавания аудиофайла: {file_path}")

    # Проверяем существование файла
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    # Отправляем запрос к API
    headers = {"xi-api-key": config.elevenlabs_api_key}

    # Правильно формируем multipart/form-data
    with open(file_path, "rb") as audio_file:
        files = {"file": (os.path.basename(file_path), audio_file, "audio/mpeg")}

        # Дополнительные параметры для API
        data = {
            "model_id": "scribe_v1",  # Используем Scribe v1 модель
            "detect_audio_events": "false",  # Выключаем определение аудио событий, таких как смех
            "diarize": "true",
        }

        # Отправка запроса
        response = requests.post(STT_API_URL, headers=headers, files=files, data=data)

        # Проверка ответа
        if response.status_code != 200:
            raise Exception(f"Ошибка API: {response.status_code} - {response.text}")

        result = response.json()
        log_info(f"Распознавание успешно завершено для файла: {file_path}")

        # Форматируем текст в JSON
        formatted_json = format_transcript_with_speakers(result)

        # Сохраняем результат в JSON-файл
        json_file_path = get_json_transcript_file_path(file_path)
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json_file.write(formatted_json)

        # Также можно сохранить человекочитаемый текст для удобства
        human_readable = generate_human_readable_transcript(result)
        text_file_path = get_transcript_file_path(file_path)
        with open(text_file_path, "w", encoding="utf-8") as text_file:
            text_file.write(human_readable)

        log_info(
            f"Результат распознавания сохранен в: {json_file_path} и {text_file_path}"
        )
        return result


def format_transcript_with_speakers(transcript_data):
    """
    Форматирует результат распознавания с учетом разных говорящих,
    сохраняя временную структуру диалога и экспортируя в JSON

    Args:
        transcript_data: Данные распознавания от API

    Returns:
        str: Форматированный JSON с транскрипцией
    """
    return safe_operation(
        _format_transcript_with_speakers_impl,
        ErrorType.TRANSCRIPTION_ERROR,
        transcript_data=transcript_data,
        default_return=json.dumps(
            {"error": "Не удалось сформировать JSON транскрипции."},
            ensure_ascii=False,
            indent=2,
        ),
    )


def _format_transcript_with_speakers_impl(transcript_data):
    """
    Внутренняя реализация форматирования результата распознавания с учетом разных говорящих

    Args:
        transcript_data: Данные распознавания от API

    Returns:
        str: Форматированный JSON с транскрипцией
    """
    # Проверяем, есть ли основной текст
    if "text" not in transcript_data:
        return json.dumps(
            {"error": "Текст не распознан."}, ensure_ascii=False, indent=2
        )

    # Создаем результирующую структуру
    result = {
        "metadata": {
            "language_code": transcript_data.get("language_code", ""),
            "language_probability": transcript_data.get("language_probability", 0),
            "full_text": transcript_data.get("text", ""),
        },
        "utterances": [],
        "audio_events": [],
    }

    # Если нет информации о словах, возвращаем только общий текст
    if "words" not in transcript_data:
        return json.dumps(result, ensure_ascii=False, indent=2)

    # Список для всех высказываний
    utterances = []

    # Текущая информация об отрезке речи
    current_utterance = None

    # Обрабатываем последовательно слова из API
    for word_info in transcript_data.get("words", []):
        # Обрабатываем аудио-события
        if word_info.get("type") == "audio_event" or "audio_event" in word_info:
            event = word_info.get("audio_event", "") or word_info.get("text", "")
            start_time = word_info.get("start", 0)
            end_time = word_info.get("end", 0)

            result["audio_events"].append(
                {"event": event, "start": start_time, "end": end_time}
            )
            continue

        # Пропускаем пробелы типа "spacing"
        if word_info.get("type") == "spacing":
            continue

        # Для обычных слов
        speaker = word_info.get("speaker_id")
        word = word_info.get("text", "")
        start_time = word_info.get("start", 0)
        end_time = word_info.get("end", 0)

        # Если это первое слово или новый говорящий
        if current_utterance is None or current_utterance["speaker"] != speaker:
            # Сохраняем предыдущее высказывание, если оно было
            if current_utterance is not None:
                utterances.append(current_utterance)

            # Начинаем новое высказывание
            current_utterance = {
                "speaker": speaker,
                "start": start_time,
                "end": end_time,
                "text": word,
            }
        else:
            # Продолжаем текущее высказывание
            current_utterance["text"] += " " + word
            current_utterance["end"] = end_time

    # Добавляем последнее высказывание
    if current_utterance is not None:
        utterances.append(current_utterance)

    # Добавляем все высказывания в результат
    result["utterances"] = utterances

    # Возвращаем JSON
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_transcript_file_path(audio_file_path):
    """
    Получает путь к файлу транскрипции на основе пути к аудиофайлу

    Args:
        audio_file_path: Путь к аудиофайлу

    Returns:
        str: Путь к файлу транскрипции
    """
    return audio_file_path.replace(".mp3", ".txt")


def get_json_transcript_file_path(audio_file_path):
    """
    Получает путь к файлу транскрипции на основе пути к аудиофайлу

    Args:
        audio_file_path: Путь к аудиофайлу

    Returns:
        str: Путь к файлу транскрипции
    """
    return audio_file_path.replace(".mp3", ".json")


def read_transcript(transcript_file_path):
    """
    Читает содержимое файла транскрипции

    Args:
        transcript_file_path: Путь к файлу транскрипции

    Returns:
        str: Содержимое файла транскрипции или пустая строка в случае ошибки
    """
    return safe_operation(
        _read_transcript_impl,
        ErrorType.FILE_ERROR,
        transcript_file_path=transcript_file_path,
        default_return="",
    )


def _read_transcript_impl(transcript_file_path):
    """
    Внутренняя реализация чтения содержимого файла транскрипции

    Args:
        transcript_file_path: Путь к файлу транскрипции

    Returns:
        str: Содержимое файла транскрипции
    """
    if os.path.exists(transcript_file_path):
        with open(transcript_file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""
