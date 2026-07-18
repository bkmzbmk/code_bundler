"""Построение графа зависимостей и обход с ограничением глубины.

Разрешение путей (по решению проекта — БЕЗ include-путей из CMake):
  C++:
    1) относительно папки текущего файла;
    2) относительно корня проекта;
    3) поиск по имени файла во всём дереве (по basename).
  Python:
    - относительные импорты (from . / from ..) — от папки файла;
    - абсолютные — сопоставляем "a.b.c" с путём "a/b/c.py"
      или пакетом "a/b/c/__init__.py" внутри проекта;
    - внешние библиотеки (не найдены в дереве) — игнорируются.
"""
from __future__ import annotations

import os
from collections import deque

from model.file_node import FileNode
from model.file_reader import read_text
from model.analyzers.analyzer_registry import AnalyzerRegistry


class DependencyGraph:
    """Разрешает зависимости и обходит граф файлов."""

    def __init__(self, root: FileNode, registry: AnalyzerRegistry) -> None:
        self._root = root
        self._root_path = os.path.abspath(root.path)
        self._registry = registry

        # Индексы для быстрого поиска файлов при разрешении путей.
        # basename(lower) -> список абсолютных путей
        self._by_basename: dict[str, list[str]] = {}
        # нормализованный абсолютный путь -> True (существует в дереве)
        self._known_abs: set[str] = set()
        self._build_index()

        # Кэш рёбер графа: abs_path -> set(abs_path зависимостей)
        self._edges: dict[str, set[str]] = {}

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------
    def resolve(self, start_files: list[str], max_depth: int) -> set[str]:
        """BFS от стартовых файлов до глубины max_depth.

        Args:
            start_files: абсолютные пути стартовых файлов.
            max_depth:   0 = только стартовые; 1 = +прямые зависимости; ...
                         Отрицательное значение = без ограничения.

        Returns:
            Множество абсолютных путей (старт + найденные зависимости).
        """
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()

        for f in start_files:
            abs_f = os.path.abspath(f)
            if abs_f not in visited:
                visited.add(abs_f)
                queue.append((abs_f, 0))

        while queue:
            current, depth = queue.popleft()
            if max_depth >= 0 and depth >= max_depth:
                continue

            for dep in self._get_dependencies(current):
                if dep not in visited:
                    visited.add(dep)
                    queue.append((dep, depth + 1))

        return visited

    def get_edges(self) -> dict[str, set[str]]:
        """Возвращает накопленный граф рёбер (для визуализации)."""
        return {k: set(v) for k, v in self._edges.items()}

    # ------------------------------------------------------------------
    # Индексация дерева
    # ------------------------------------------------------------------
    def _build_index(self) -> None:
        for node in self._root.iter_files():
            abs_path = os.path.normcase(os.path.abspath(node.path))
            self._known_abs.add(abs_path)
            base = node.name.lower()
            self._by_basename.setdefault(base, []).append(
                os.path.abspath(node.path)
            )

    # ------------------------------------------------------------------
    # Получение зависимостей одного файла (с кэшем)
    # ------------------------------------------------------------------
    def _get_dependencies(self, abs_path: str) -> set[str]:
        if abs_path in self._edges:
            return self._edges[abs_path]

        analyzer = self._registry.get_for(abs_path)
        if analyzer is None or not os.path.isfile(abs_path):
            self._edges[abs_path] = set()
            return self._edges[abs_path]

        try:
            source = read_text(abs_path)
        except OSError:
            self._edges[abs_path] = set()
            return self._edges[abs_path]

        raw_deps = analyzer.extract_dependencies(abs_path, source)

        ext = os.path.splitext(abs_path)[1].lower()
        resolved: set[str] = set()
        for raw in raw_deps:
            target = self._resolve_raw(abs_path, raw, ext)
            if target is not None:
                resolved.add(target)

        self._edges[abs_path] = resolved
        return resolved

    # ------------------------------------------------------------------
    # Разрешение сырой зависимости -> абсолютный путь (или None)
    # ------------------------------------------------------------------
    def _resolve_raw(self, from_file: str, raw: str, ext: str) -> str | None:
        from config import CPP_EXTENSIONS, PYTHON_EXTENSIONS

        if ext in CPP_EXTENSIONS:
            return self._resolve_cpp(from_file, raw)
        if ext in PYTHON_EXTENSIONS:
            return self._resolve_python(from_file, raw)
        return None

    # ---- C++ ----
    def _resolve_cpp(self, from_file: str, inc: str) -> str | None:
        from_dir = os.path.dirname(from_file)

        # 1) относительно папки текущего файла
        candidate = os.path.abspath(os.path.join(from_dir, inc))
        if self._exists(candidate):
            return candidate

        # 2) относительно корня проекта
        candidate = os.path.abspath(os.path.join(self._root_path, inc))
        if self._exists(candidate):
            return candidate

        # 3) поиск по basename во всём дереве
        base = os.path.basename(inc).lower()
        matches = self._by_basename.get(base, [])
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # Несколько файлов с таким именем — пытаемся выбрать тот,
            # чей относительный путь заканчивается на inc.
            inc_norm = inc.replace("\\", "/").lower()
            for m in matches:
                if m.replace("\\", "/").lower().endswith(inc_norm):
                    return m
            # Не смогли однозначно — берём первый (лучше, чем ничего).
            return matches[0]

        return None

    # ---- Python ----
    def _resolve_python(self, from_file: str, mod: str) -> str | None:
        # Относительные импорты: ведущие точки
        if mod.startswith("."):
            return self._resolve_python_relative(from_file, mod)
        return self._resolve_python_absolute(mod)

    def _resolve_python_relative(self, from_file: str, mod: str) -> str | None:
        level = len(mod) - len(mod.lstrip("."))
        rest = mod[level:]  # часть после точек

        base_dir = os.path.dirname(from_file)
        # Каждая точка сверх первой поднимает на уровень выше
        for _ in range(level - 1):
            base_dir = os.path.dirname(base_dir)

        parts = rest.split(".") if rest else []
        target = os.path.join(base_dir, *parts) if parts else base_dir
        return self._python_path_from_target(target)

    def _resolve_python_absolute(self, mod: str) -> str | None:
        parts = mod.split(".")
        # Пробуем от корня проекта, срезая хвост
        # (mod может включать имя объекта, а не только модуля)
        for cut in range(len(parts), 0, -1):
            sub = parts[:cut]
            target = os.path.join(self._root_path, *sub)
            found = self._python_path_from_target(target)
            if found:
                return found
        return None

    def _python_path_from_target(self, target_no_ext: str) -> str | None:
        """Пробует target.py и target/__init__.py."""
        py_file = target_no_ext + ".py"
        if self._exists(py_file):
            return os.path.abspath(py_file)
        init_file = os.path.join(target_no_ext, "__init__.py")
        if self._exists(init_file):
            return os.path.abspath(init_file)
        return None

    # ------------------------------------------------------------------
    def _exists(self, abs_path: str) -> bool:
        """Файл есть в проекте (сверяем с индексом дерева)."""
        norm = os.path.normcase(os.path.abspath(abs_path))
        return norm in self._known_abs