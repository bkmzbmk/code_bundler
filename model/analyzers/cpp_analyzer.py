"""Анализатор зависимостей C/C++: парсинг #include "...".

Системные include (<...>) игнорируем — так решено в проекте."""
from __future__ import annotations

import re

from config import CPP_EXTENSIONS
from model.analyzers.base_analyzer import IDependencyAnalyzer


class CppAnalyzer(IDependencyAnalyzer):
    """Извлекает пути из директив #include "...".

    Пример:
        #include "core/engine.h"   -> "core/engine.h"
        #include <vector>          -> ИГНОРИРУЕТСЯ
    """

    # #include с двойными кавычками. Разрешаем пробелы после #.
    _INCLUDE_RE = re.compile(
        r'^\s*#\s*include\s*"([^"]+)"',
        re.MULTILINE,
    )

    def supported_extensions(self) -> set[str]:
        return set(CPP_EXTENSIONS)

    def extract_dependencies(self, file_path: str, source: str) -> list[str]:
        source = self._strip_comments(source)
        deps: list[str] = []
        for match in self._INCLUDE_RE.finditer(source):
            inc = match.group(1).strip().replace("\\", "/")
            if inc:
                deps.append(inc)
        return deps

    @staticmethod
    def _strip_comments(source: str) -> str:
        """Убирает комментарии, чтобы не ловить #include из них.

        Простые эвристики (без учёта строковых литералов) —
        для анализа зависимостей этого достаточно."""
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
        source = re.sub(r"//.*", "", source)
        return source