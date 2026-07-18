"""Фасад над всей логикой Model. Единая точка входа для Presenter.

Этап 1: загрузка проекта, сборка, подсчёт токенов — готово.
Этап 2: resolve_dependencies — РАБОЧИЙ (граф зависимостей).
Профили — заглушки (позже)."""
from __future__ import annotations

import os

from config import (
    DEFAULT_IGNORE, CODE_EXTENSIONS, DEFAULT_TOKEN_LIMIT,
    HISTORY_FILE, HISTORY_MAX_ITEMS, DEFAULT_ACTIVE_EXTENSIONS,
)
from model.folder_history import FolderHistory
from model.file_node import FileNode
from model.ignore_rules import IgnoreRules
from model.project_scanner import ProjectScanner
from model.bundler import Bundler
from model.token_counter import TokenCounter

from model.analyzers.analyzer_registry import AnalyzerRegistry
from model.analyzers.cpp_analyzer import CppAnalyzer
from model.analyzers.python_analyzer import PythonAnalyzer
from model.dependency_graph import DependencyGraph


class AppModel:
    """Фасад Model. Прячет внутренние классы за простыми методами."""

    def __init__(self) -> None:
        self._ignore = IgnoreRules(set(DEFAULT_IGNORE))
        self._scanner = ProjectScanner(self._ignore, CODE_EXTENSIONS)

        # Активные расширения (изменяются пользователем через GUI).
        # Порядок для отображения храним отдельно (list), а фильтр —
        # как множество внутри сканера.
        self._active_extensions: set[str] = {
            e.lower() for e in DEFAULT_ACTIVE_EXTENSIONS
        }
        self._scanner.set_extensions(self._active_extensions)
        # Все расширения, найденные в текущем проекте (для GUI-списка).
        self._all_extensions: set[str] = set()

        self._token_counter = TokenCounter()

        # История открытых папок (персистентная)
        self._history = FolderHistory(HISTORY_FILE, HISTORY_MAX_ITEMS)

        # Реестр анализаторов (расширяемо: добавить язык — register)
        self._registry = AnalyzerRegistry()
        self._registry.register(CppAnalyzer())
        self._registry.register(PythonAnalyzer())

        self._root_node: FileNode | None = None
        self._root_path: str | None = None
        self._graph: DependencyGraph | None = None

        self.token_limit: int = DEFAULT_TOKEN_LIMIT

        self._all_extensions: set[str] = {
            e.lower() for e in DEFAULT_ACTIVE_EXTENSIONS
        }

    # ------------------------------------------------------------------
    # Проект
    # ------------------------------------------------------------------

    def load_project(self, root_path: str) -> FileNode:
        """Сканирует папку, строит дерево и граф зависимостей."""
        self._root_path = os.path.abspath(root_path)

        # Собираем ВСЕ расширения проекта (для предложения в GUI).
        found = self._scanner.collect_extensions(self._root_path)
        # Дефолтные расширения всегда присутствуют в списке выбора,
        # даже если в проекте их нет (чтобы можно было отметить).
        self._all_extensions = set(found) | {
            e.lower() for e in DEFAULT_ACTIVE_EXTENSIONS
        }

        # Сканируем дерево под активные расширения.
        self._scanner.set_extensions(self._active_extensions)
        self._root_node = self._scanner.scan(self._root_path)
        self._graph = DependencyGraph(self._root_node, self._registry)
        self._history.add(self._root_path)
        return self._root_node

    def get_root_node(self) -> FileNode | None:
        return self._root_node

    def get_root_path(self) -> str | None:
        return self._root_path

    # ------------------------------------------------------------------
    # История папок
    # ------------------------------------------------------------------
    def get_folder_history(self) -> list[str]:
        """Список недавних папок (свежая — первой)."""
        return self._history.get_all()

    def remove_from_history(self, path: str) -> None:
        self._history.remove(path)

    def clear_history(self) -> None:
        self._history.clear()

    # ------------------------------------------------------------------
    # Расширения файлов
    # ------------------------------------------------------------------
    def get_all_extensions(self) -> list[str]:
        """Все расширения проекта + дефолтные, отсортированные."""
        return sorted(self._all_extensions)

    def get_active_extensions(self) -> set[str]:
        """Текущий набор активных (отмеченных) расширений."""
        return set(self._active_extensions)

    def set_active_extensions(self, extensions: set[str]) -> FileNode | None:
        """Задать активные расширения и пересканировать проект.

        Returns:
            Новый корневой FileNode (если проект был загружен), иначе None.
        """
        self._active_extensions = {e.lower() for e in extensions}
        if self._root_path is None:
            return None
        # Пересканируем дерево и перестроим граф под новый фильтр.
        self._scanner.set_extensions(self._active_extensions)
        self._root_node = self._scanner.scan(self._root_path)
        self._graph = DependencyGraph(self._root_node, self._registry)
        return self._root_node

    # ------------------------------------------------------------------
    # Зависимости (Этап 2)
    # ------------------------------------------------------------------
    def resolve_dependencies(
        self, selected_rel_paths: list[str], max_depth: int
    ) -> list[str]:
        """Возвращает выбранные файлы + их зависимости до max_depth.

        Args:
            selected_rel_paths: относительные пути выбранных файлов.
            max_depth: 0 = только выбранные; 1 = +прямые; -1 = без лимита.

        Returns:
            Отсортированный список относительных путей (уникальных).
        """
        if self._graph is None or self._root_path is None:
            return list(selected_rel_paths)

        start_abs = [
            os.path.join(self._root_path, rp.replace("/", os.sep))
            for rp in selected_rel_paths
        ]
        resolved_abs = self._graph.resolve(start_abs, max_depth)

        rel_paths = [
            os.path.relpath(p, self._root_path).replace("\\", "/")
            for p in resolved_abs
        ]
        return sorted(set(rel_paths))

    def get_dependency_edges(self) -> dict[str, set[str]]:
        """Граф рёбер в относительных путях (для отладки/визуализации)."""
        if self._graph is None or self._root_path is None:
            return {}
        edges = self._graph.get_edges()
        result: dict[str, set[str]] = {}
        for src, targets in edges.items():
            src_rel = os.path.relpath(src, self._root_path).replace("\\", "/")
            result[src_rel] = {
                os.path.relpath(t, self._root_path).replace("\\", "/")
                for t in targets
            }
        return result

    # ------------------------------------------------------------------
    # Сборка и токены
    # ------------------------------------------------------------------
    def build_bundle(
        self,
        rel_paths: list[str],
        strip_comments: bool = False,
        strip_blank: bool = False,
    ) -> str:
        if self._root_path is None:
            raise RuntimeError("Проект не загружен (нет корневого пути).")

        abs_paths = [
            os.path.join(self._root_path, rp.replace("/", os.sep))
            for rp in rel_paths
        ]
        bundler = Bundler(strip_comments=strip_comments,
                          strip_blank_lines=strip_blank)
        return bundler.bundle(abs_paths, self._root_path)

    def count_tokens(self, text: str) -> int:
        return self._token_counter.count(text)

    def tokens_available(self) -> bool:
        return self._token_counter.is_available()