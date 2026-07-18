"""Реестр анализаторов: отдаёт нужный по расширению файла."""
from __future__ import annotations

import os

from model.analyzers.base_analyzer import IDependencyAnalyzer


class AnalyzerRegistry:
    """Хранит анализаторы и выбирает подходящий по расширению."""

    def __init__(self) -> None:
        # ext -> analyzer
        self._by_ext: dict[str, IDependencyAnalyzer] = {}

    def register(self, analyzer: IDependencyAnalyzer) -> None:
        for ext in analyzer.supported_extensions():
            self._by_ext[ext.lower()] = analyzer

    def get_for(self, file_path: str) -> IDependencyAnalyzer | None:
        ext = os.path.splitext(file_path)[1].lower()
        return self._by_ext.get(ext)

    def has_analyzer_for(self, file_path: str) -> bool:
        return self.get_for(file_path) is not None