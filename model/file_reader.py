"""Чтение файлов с автоопределением кодировки."""
from __future__ import annotations

from config import FILE_ENCODINGS


def read_text(path: str) -> str:
    """Читает текстовый файл, перебирая кодировки из FILE_ENCODINGS.

    Возвращает содержимое. Если ничего не подошло — читает с
    заменой ошибочных байтов (errors='replace')."""
    last_error: Exception | None = None
    for enc in FILE_ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            continue
    # Последняя попытка — с заменой битых символов
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()