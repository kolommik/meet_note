import os
import requests
import json
from dotenv import load_dotenv
from .logger import log_info, log_error

# Загрузка переменных окружения
load_dotenv()

# Получение API ключа из переменных окружения
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

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
    lines = []

    # Если нет информации о словах, возвращаем только общий текст
    if "words" not in transcript_data:
        lines.append(transcript_data.get("text", "Text not recognized."))
        return "\n".join(lines)

    # Список аудио-событий
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

    # Добавляем аудио-события в начало, если они есть
    if audio_events:
        lines.insert(0, " ".join(audio_events))
        lines.insert(1, "")

    return "\n".join(lines)


def format_time(seconds):
    """
    Форматирует время в секундах в формат MM:SS.mmm

    Args:
        seconds: Время в секундах

    Returns:
        str: Отформатированное время
    """
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:06.3f}"


def transcribe_audio(file_path):
    """
    Отправляет аудиофайл в ElevenLabs API для распознавания речи

    Args:
        file_path: Путь к аудиофайлу для распознавания
        max_speakers: Максимальное количество говорящих для диаризации (по умолчанию 5)

    Returns:
        dict: Словарь с результатами распознавания или None в случае ошибки
    """
    if not ELEVENLABS_API_KEY:
        log_error("API ключ ElevenLabs не найден в переменных окружения")
        return None

    log_info(f"Начало распознавания аудиофайла: {file_path}")

    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            log_error(f"Файл не найден: {file_path}")
            return None

        # Отправляем запрос к API
        headers = {"xi-api-key": ELEVENLABS_API_KEY}

        # Правильно формируем multipart/form-data
        with open(file_path, "rb") as audio_file:
            files = {"file": (os.path.basename(file_path), audio_file, "audio/mpeg")}

            # Дополнительные параметры для API
            data = {
                "model_id": "scribe_v1",  # Используем Scribe v1 модель
                "detect_audio_events": "true",  # Включаем определение аудио событий, таких как смех
                "diarize": "true",
            }

            # Отправка запроса
            response = requests.post(
                STT_API_URL, headers=headers, files=files, data=data
            )

            # Проверка ответа
            if response.status_code == 200:
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
            else:
                log_error(f"Ошибка API: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        log_error(f"Ошибка при распознавании аудио: {str(e)}")
        return None


def format_transcript_with_speakers(transcript_data):
    """
    Форматирует результат распознавания с учетом разных говорящих,
    сохраняя временную структуру диалога и экспортируя в JSON

    Args:
        transcript_data: Данные распознавания от API

    Returns:
        str: Форматированный JSON с транскрипцией
    """
    try:
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

    except Exception as e:
        return json.dumps(
            {"error": f"Ошибка форматирования транскрипции: {str(e)}"},
            ensure_ascii=False,
            indent=2,
        )


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
    try:
        if os.path.exists(transcript_file_path):
            with open(transcript_file_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""
    except Exception as e:
        log_error(f"Ошибка при чтении файла транскрипции: {str(e)}")
        return ""
