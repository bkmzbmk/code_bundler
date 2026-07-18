"""Подсчёт токенов через tiktoken с fallback на грубую оценку."""
from __future__ import annotations

from config import (
    DEFAULT_TIKTOKEN_MODEL,
    FALLBACK_CHARS_PER_TOKEN,
)


class TokenCounter:
    """Считает токены. Если tiktoken не установлен — оценивает
    по количеству символов."""

    def __init__(self, encoding_name: str = DEFAULT_TIKTOKEN_MODEL) -> None:
        self._encoding = None
        self._available = False
        try:
            import tiktoken  # ленивый импорт
            self._encoding = tiktoken.get_encoding(encoding_name)
            self._available = True
        except Exception:
            self._encoding = None
            self._available = False

    def is_available(self) -> bool:
        """True, если используется точный подсчёт (tiktoken доступен)."""
        return self._available

    def count(self, text: str) -> int:
        """Возвращает число токенов (точное или оценочное)."""
        if not text:
            return 0
        if self._available and self._encoding is not None:
            return len(self._encoding.encode(text))
        # Грубая оценка
        return max(1, len(text) // FALLBACK_CHARS_PER_TOKEN)