"""
Модуль для централизованного управления статистикой использования LLM.
Содержит функции для инициализации, обновления и получения статистики
использования различных LLM моделей.
"""

import streamlit as st
from utils.logger import log_info


def initialize_llm_stats():
    """
    Инициализирует статистику использования LLM в session_state.
    Вызывается один раз при запуске приложения.
    """
    if "total_llm_cost" not in st.session_state:
        st.session_state.total_llm_cost = 0.0
        st.session_state.total_input_tokens = 0
        st.session_state.total_output_tokens = 0
        st.session_state.total_cache_create_tokens = 0
        st.session_state.total_cache_read_tokens = 0
        st.session_state.total_calls = 0
        log_info("Статистика LLM инициализирована")


def update_llm_stats(llm_strategy, model_name):
    """
    Обновляет общую статистику использования LLM после каждого запроса.

    Args:
        llm_strategy: Стратегия для взаимодействия с LLM
        model_name: Название модели
        provider: Название провайдера

    Returns:
        dict: Словарь с текущей статистикой для данного запроса
    """
    # Убедимся, что статистика инициализирована
    initialize_llm_stats()

    # Получаем данные о текущем запросе
    current_input_tokens = llm_strategy.get_input_tokens()
    current_output_tokens = llm_strategy.get_output_tokens()
    current_cache_create_tokens = llm_strategy.get_cache_create_tokens()
    current_cache_read_tokens = llm_strategy.get_cache_read_tokens()
    current_price = llm_strategy.get_full_price()

    # Обновляем общую статистику
    st.session_state.total_llm_cost += current_price
    st.session_state.total_input_tokens += current_input_tokens
    st.session_state.total_output_tokens += current_output_tokens
    st.session_state.total_cache_create_tokens += current_cache_create_tokens
    st.session_state.total_cache_read_tokens += current_cache_read_tokens
    st.session_state.total_calls += 1

    # Создаем и возвращаем статистику текущего запроса
    llm_stats = {
        "input_tokens": current_input_tokens,
        "output_tokens": current_output_tokens,
        "cache_create_tokens": current_cache_create_tokens,
        "cache_read_tokens": current_cache_read_tokens,
        "full_price": current_price,
        "model": model_name,
    }

    log_info(f"Обновлена статистика LLM: {model_name}, {current_price:.6f}$")
    return llm_stats


def get_total_llm_stats():
    """
    Возвращает общую статистику использования LLM.

    Returns:
        dict: Словарь с общей статистикой использования LLM
    """
    # Убедимся, что статистика инициализирована
    initialize_llm_stats()

    return {
        "total_cost": st.session_state.total_llm_cost,
        "total_input_tokens": st.session_state.total_input_tokens,
        "total_output_tokens": st.session_state.total_output_tokens,
        "total_cache_create_tokens": st.session_state.total_cache_create_tokens,
        "total_cache_read_tokens": st.session_state.total_cache_read_tokens,
        "total_calls": st.session_state.total_calls,
    }


def reset_llm_stats():
    """
    Сбрасывает всю статистику использования LLM.
    """
    st.session_state.total_llm_cost = 0.0
    st.session_state.total_input_tokens = 0
    st.session_state.total_output_tokens = 0
    st.session_state.total_cache_create_tokens = 0
    st.session_state.total_cache_read_tokens = 0
    st.session_state.total_calls = 0
    log_info("Статистика LLM сброшена")
