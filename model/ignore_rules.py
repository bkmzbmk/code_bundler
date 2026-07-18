"""Правила игнорирования путей (build/, .git/ и т.п.).

Объединяет два источника:
  1) встроенные паттерны (DEFAULT_IGNORE) — по имени компонента пути;
  2) правила из .gitignore (если подключены) — по относительному пути.
"""
from __future__ import annotations

import fnmatch
import os

from model.gitignore_rules import GitignoreRules


class IgnoreRules:
    """Проверяет, нужно ли игнорировать файл/папку.

    Поддерживает точные имена и glob-паттерны (cmake-build-*),
    а также правила .gitignore (опционально)."""

    def __init__(self, patterns: set[str]) -> None:
        self._patterns: set[str] = set(patterns)
        self._gitignore: GitignoreRules | None = None

    def add(self, pattern: str) -> None:
        self._patterns.add(pattern)

    def set_gitignore(self, gitignore: GitignoreRules | None) -> None:
        """Подключить (или сбросить) правила .gitignore."""
        self._gitignore = gitignore

    def has_gitignore(self) -> bool:
        return self._gitignore is not None and self._gitignore.has_rules()

    # ------------------------------------------------------------------
    def is_ignored(self, path: str) -> bool:
        """Проверка по имени компонента пути (встроенные паттерны).

        Сохранена для обратной совместимости. Не учитывает .gitignore
        (для него нужен относительный путь — см. is_ignored_rel)."""
        parts = os.path.normpath(path).split(os.sep)
        for part in parts:
            if not part:
                continue
            for pattern in self._patterns:
                if part == pattern or fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def is_ignored_rel(self, path: str, rel_path: str, is_dir: bool) -> bool:
        """Полная проверка: встроенные паттерны + .gitignore.

        Args:
            path:     абсолютный путь (для встроенных паттернов).
            rel_path: путь относительно корня проекта ("/"-разделитель).
            is_dir:   является ли путь папкой.
        """
        if self.is_ignored(path):
            return True
        if self._gitignore is not None:
            if self._gitignore.is_ignored(rel_path, is_dir):
                return True
        return False