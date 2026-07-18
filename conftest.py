"""Настройки pytest: sys.path + пропуск GUI-тестов без дисплея (CI)
+ изоляция файла истории папок от реального диска."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _has_display() -> bool:
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY"))
    return True


collect_ignore_glob = []
if not _has_display():
    collect_ignore_glob.append("test/test_view*.py")
    collect_ignore_glob.append("test/*gui*.py")


@pytest.fixture(autouse=True)
def _isolate_history(tmp_path, monkeypatch):
    """Каждый тест использует свой временный файл истории.

    Патчим config.HISTORY_FILE И уже импортированную ссылку в
    model.app_model (т.к. AppModel импортировал HISTORY_FILE по
    значению)."""
    hist = str(tmp_path / "history_isolated.json")
    monkeypatch.setattr("config.HISTORY_FILE", hist, raising=False)
    monkeypatch.setattr(
        "model.app_model.HISTORY_FILE", hist, raising=False
    )
    yield