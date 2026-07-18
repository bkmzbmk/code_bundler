"""Анализатор зависимостей Python: парсинг import / from ... import.

Используем модуль ast (надёжнее regex). При синтаксической ошибке
файла — падаем на regex-эвристику."""
from __future__ import annotations

import ast
import re

from config import PYTHON_EXTENSIONS
from model.analyzers.base_analyzer import IDependencyAnalyzer


class PythonAnalyzer(IDependencyAnalyzer):
    """Извлекает имена импортируемых модулей.

    Возвращает "точечные" имена, как в исходнике:
        import mypkg.utils          -> "mypkg.utils"
        from mypkg import helpers   -> "mypkg" (+ уровень для relative)
        from . import sibling       -> ".sibling" (относительный)
        from ..core import engine   -> "..core"
    Разрешение в реальные пути — в DependencyGraph."""

    def supported_extensions(self) -> set[str]:
        return set(PYTHON_EXTENSIONS)

    def extract_dependencies(self, file_path: str, source: str) -> list[str]:
        try:
            return self._extract_with_ast(source)
        except SyntaxError:
            return self._extract_with_regex(source)

    # ------------------------------------------------------------------
    def _extract_with_ast(self, source: str) -> list[str]:
        tree = ast.parse(source)
        deps: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # import a.b.c, d
                for alias in node.names:
                    deps.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                # from X import ...   /   from . import ...
                level = node.level          # 0=абсолютный, >=1 относительный
                module = node.module or ""  # может быть None (from . import x)
                prefix = "." * level
                if module:
                    deps.append(prefix + module)
                else:
                    # from . import name  -> считаем зависимостью пакет уровня
                    for alias in node.names:
                        deps.append(prefix + alias.name)

        return deps

    # ------------------------------------------------------------------
    _IMPORT_RE = re.compile(r"^\s*import\s+([\w\.]+)", re.MULTILINE)
    _FROM_RE = re.compile(r"^\s*from\s+(\.*[\w\.]*)\s+import", re.MULTILINE)

    def _extract_with_regex(self, source: str) -> list[str]:
        """Fallback, если ast не смог распарсить (битый синтаксис)."""
        deps: list[str] = []
        for m in self._IMPORT_RE.finditer(source):
            deps.append(m.group(1))
        for m in self._FROM_RE.finditer(source):
            mod = m.group(1)
            if mod:
                deps.append(mod)
        return deps