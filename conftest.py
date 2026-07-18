"""Настройки pytest: sys.path + пропуск GUI-тестов без дисплея (CI)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _has_display() -> bool:
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY"))
    return True


collect_ignore_glob = []
if not _has_display():
    collect_ignore_glob.append("test/test_view*.py")
    collect_ignore_glob.append("test/*gui*.py")