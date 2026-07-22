"""Правила игнорирования путей (build/, .git/ и т.п.).

Объединяет три источника:
  1) встроенные паттерны (DEFAULT_IGNORE) — по имени компонента пути;
  2) правила из .gitignore (если подключены) — по относительному пути;
  3) пользовательские исключённые папки — по относительному пути
     (папка и всё её содержимое).
"""
from __future__ import annotations

import fnmatch
import os

from model.gitignore_rules import GitignoreRules


class IgnoreRules:
    """Проверяет, нужно ли игнорировать файл/папку."""

    def __init__(self, patterns: set[str]) -> None:
        self._patterns: set[str] = set(patterns)
        self._gitignore: GitignoreRules | None = None
        # Пользовательские исключённые папки: относительные пути
        # с "/" разделителем, без ведущего/хвостового слэша.
        self._excluded_dirs: set[str] = set()

    def add(self, pattern: str) -> None:
        self._patterns.add(pattern)

    def set_gitignore(self, gitignore: GitignoreRules | None) -> None:
        """Подключить (или сбросить) правила .gitignore."""
        self._gitignore = gitignore

    def has_gitignore(self) -> bool:
        return self._gitignore is not None and self._gitignore.has_rules()

    # ------------------------------------------------------------------
    # Пользовательские исключённые папки
    # ------------------------------------------------------------------
    def set_excluded_dirs(self, rel_dirs: set[str]) -> None:
        """Задать набор исключённых папок (относительные пути)."""
        self._excluded_dirs = {self._norm_rel(d) for d in rel_dirs if d}

    def get_excluded_dirs(self) -> set[str]:
        return set(self._excluded_dirs)

    def add_excluded_dir(self, rel_dir: str) -> None:
        norm = self._norm_rel(rel_dir)
        if norm:
            self._excluded_dirs.add(norm)

    def remove_excluded_dir(self, rel_dir: str) -> None:
        self._excluded_dirs.discard(self._norm_rel(rel_dir))

    @staticmethod
    def _norm_rel(rel: str) -> str:
        """Нормализует относительный путь: '/' разделитель, без краёв."""
        return rel.replace("\\", "/").strip("/")

    def _is_in_excluded_dir(self, rel_path: str) -> bool:
        """True, если rel_path — исключённая папка или лежит внутри неё."""
        if not self._excluded_dirs:
            return False
        rel = self._norm_rel(rel_path)
        for ex in self._excluded_dirs:
            # Точное совпадение (сама папка) ИЛИ путь внутри неё.
            if rel == ex or rel.startswith(ex + "/"):
                return True
        return False

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
        """Полная проверка: встроенные паттерны + .gitignore +
        пользовательские исключённые папки.

        Args:
            path:     абсолютный путь (для встроенных паттернов).
            rel_path: путь относительно корня проекта ("/"-разделитель).
            is_dir:   является ли путь папкой.
        """
        # Пользовательские исключённые папки — приоритетнее всего.
        if self._is_in_excluded_dir(rel_path):
            return True
        if self.is_ignored(path):
            return True
        if self._gitignore is not None:
            if self._gitignore.is_ignored(rel_path, is_dir):
                return True
        return False