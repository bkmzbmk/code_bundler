"""Тесты TokenCounter (в т.ч. поведение fallback без tiktoken)."""
from config import FALLBACK_CHARS_PER_TOKEN
from model.token_counter import TokenCounter


def test_empty_text_is_zero():
    tc = TokenCounter()
    assert tc.count("") == 0


def test_count_positive():
    tc = TokenCounter()
    assert tc.count("hello world foo bar") > 0


def test_is_available_returns_bool():
    tc = TokenCounter()
    assert isinstance(tc.is_available(), bool)


def test_fallback_estimation(monkeypatch):
    """Форсируем режим fallback (tiktoken 'недоступен')."""
    tc = TokenCounter()
    # Симулируем отсутствие tiktoken
    tc._available = False
    tc._encoding = None

    text = "x" * (FALLBACK_CHARS_PER_TOKEN * 10)
    # Грубая оценка: len // FALLBACK_CHARS_PER_TOKEN
    assert tc.count(text) == 10


def test_fallback_min_one_token():
    tc = TokenCounter()
    tc._available = False
    tc._encoding = None
    # Короткий текст -> минимум 1 токен
    assert tc.count("ab") == 1


def test_exact_mode_if_available():
    tc = TokenCounter()
    if not tc.is_available():
        # tiktoken не установлен в окружении — пропускаем
        import pytest
        pytest.skip("tiktoken недоступен в этом окружении")
    # Точный подсчёт должен давать положительное число
    assert tc.count("def foo(): pass") > 0