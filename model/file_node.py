"""Узел дерева файлов проекта."""
from __future__ import annotations

import os
from typing import Iterator, Optional


class FileNode:
    """Узел дерева файлов/папок проекта.

    Хранит абсолютный и относительный (от корня проекта) пути.
    Для GUI используется поле `selected` (чекбоксы)."""

    def __init__(
        self,
        path: str,
        rel_path: str,
        is_dir: bool,
        parent: Optional["FileNode"] = None,
    ) -> None:
        self.path: str = path              # абсолютный путь
        self.rel_path: str = rel_path      # путь относительно корня проекта
        self.name: str = os.path.basename(path.rstrip(os.sep)) or path
        self.is_dir: bool = is_dir
        self.parent: Optional[FileNode] = parent
        self.children: list[FileNode] = []
        self.selected: bool = False

    def add_child(self, child: "FileNode") -> None:
        """Добавить дочерний узел."""
        child.parent = self
        self.children.append(child)

    def iter_files(self) -> Iterator["FileNode"]:
        """Рекурсивный обход: только файлы (не папки)."""
        if not self.is_dir:
            yield self
        for child in self.children:
            yield from child.iter_files()

    def iter_all(self) -> Iterator["FileNode"]:
        """Рекурсивный обход: все узлы (файлы и папки)."""
        yield self
        for child in self.children:
            yield from child.iter_all()

    def find_by_rel_path(self, rel_path: str) -> Optional["FileNode"]:
        """Найти узел по относительному пути (нормализуем разделители)."""
        target = rel_path.replace("\\", "/")
        for node in self.iter_all():
            if node.rel_path.replace("\\", "/") == target:
                return node
        return None

    def __repr__(self) -> str:
        kind = "DIR" if self.is_dir else "FILE"
        return f"<FileNode {kind} {self.rel_path!r}>"