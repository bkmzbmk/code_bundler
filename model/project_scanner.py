"""Сканирование папки проекта и построение дерева FileNode."""
from __future__ import annotations

import os

from model.file_node import FileNode
from model.ignore_rules import IgnoreRules
from model.gitignore_rules import GitignoreRules


class ProjectScanner:
    """Строит дерево FileNode из папки проекта.

    Игнорирует пути по IgnoreRules (встроенные паттерны + .gitignore).
    Может фильтровать по расширениям (только выбранные)."""

    GITIGNORE_NAME = ".gitignore"

    def __init__(
        self,
        ignore_rules: IgnoreRules,
        code_extensions: set[str] | None = None,
        use_gitignore: bool = True,
    ) -> None:
        self._ignore = ignore_rules
        # None -> без фильтра (все файлы). Иначе множество расширений.
        self._code_extensions = (
            {e.lower() for e in code_extensions}
            if code_extensions is not None else None
        )
        self._use_gitignore = use_gitignore

    def set_extensions(self, code_extensions: set[str] | None) -> None:
        """Задать активный набор расширений (None = все файлы)."""
        self._code_extensions = (
            {e.lower() for e in code_extensions}
            if code_extensions is not None else None
        )

    # ------------------------------------------------------------------
    def scan(self, root_path: str) -> FileNode:
        """Возвращает корневой FileNode со всем деревом.

        Пустые папки (без подходящих файлов) отбрасываются.
        Если в корне есть .gitignore — его правила подключаются."""
        root_path = os.path.abspath(root_path)
        if not os.path.isdir(root_path):
            raise ValueError(f"Путь не является папкой: {root_path}")

        self._apply_gitignore(root_path)

        root_node = FileNode(path=root_path, rel_path="", is_dir=True)
        self._scan_dir(root_path, root_node, root_path)
        return root_node

    def collect_extensions(self, root_path: str) -> set[str]:
        """Возвращает ВСЕ расширения файлов проекта (кроме игнора).

        Проходит папку с учётом IgnoreRules/.gitignore, но БЕЗ фильтра
        по расширениям. Файлы без расширения игнорируются."""
        root_path = os.path.abspath(root_path)
        if not os.path.isdir(root_path):
            return set()

        self._apply_gitignore(root_path)

        found: set[str] = set()
        self._collect_ext_dir(root_path, root_path, found)
        return found

    # ------------------------------------------------------------------
    # Внутреннее
    # ------------------------------------------------------------------
    def _apply_gitignore(self, root_path: str) -> None:
        """Подключает .gitignore из корня (если включено и есть)."""
        if self._use_gitignore:
            gi_path = os.path.join(root_path, self.GITIGNORE_NAME)
            gitignore = GitignoreRules.from_file(gi_path)
            self._ignore.set_gitignore(
                gitignore if gitignore.has_rules() else None
            )
        else:
            self._ignore.set_gitignore(None)

    def _scan_dir(
        self, dir_path: str, parent_node: FileNode, root_path: str
    ) -> None:
        """Рекурсивно наполняет parent_node содержимым dir_path."""
        try:
            entries = sorted(
                os.scandir(dir_path),
                key=lambda e: (not e.is_dir(), e.name.lower()),
            )
        except (PermissionError, OSError):
            return

        for entry in entries:
            rel = os.path.relpath(entry.path, root_path).replace("\\", "/")
            is_dir = entry.is_dir(follow_symlinks=False)

            if self._ignore.is_ignored_rel(entry.path, rel, is_dir):
                continue

            if is_dir:
                dir_node = FileNode(entry.path, rel, is_dir=True)
                self._scan_dir(entry.path, dir_node, root_path)
                if dir_node.children:
                    parent_node.add_child(dir_node)
            else:
                if self._is_code_file(entry.name):
                    file_node = FileNode(entry.path, rel, is_dir=False)
                    parent_node.add_child(file_node)

    def _collect_ext_dir(
        self, dir_path: str, root_path: str, found: set[str]
    ) -> None:
        """Рекурсивный сбор расширений с учётом игноров."""
        try:
            entries = list(os.scandir(dir_path))
        except (PermissionError, OSError):
            return

        for entry in entries:
            rel = os.path.relpath(entry.path, root_path).replace("\\", "/")
            is_dir = entry.is_dir(follow_symlinks=False)

            if self._ignore.is_ignored_rel(entry.path, rel, is_dir):
                continue

            if is_dir:
                self._collect_ext_dir(entry.path, root_path, found)
            else:
                ext = os.path.splitext(entry.name)[1].lower()
                if ext:  # файлы без расширения пропускаем
                    found.add(ext)

    def _is_code_file(self, filename: str) -> bool:
        if self._code_extensions is None:
            return True
        ext = os.path.splitext(filename)[1].lower()
        return ext in self._code_extensions