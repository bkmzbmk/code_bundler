"""Настройки pytest: пропуск GUI-тестов без дисплея (headless CI)."""
import os
import sys

import pytest

# Гарантируем, что корень проекта в sys.path (импорты model/view/...).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _has_display() -> bool:
    # Linux: нужен X-дисплей. Windows/macOS обычно ок.
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY"))
    return True


collect_ignore_glob = []
if not _has_display():
    # Не собираем тесты, требующие GUI (если такие появятся).
    collect_ignore_glob.append("test/test_view*.py")
    collect_ignore_glob.append("test/*gui*.py")