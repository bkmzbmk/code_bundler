"""Интерфейс анализатора зависимостей для одного языка."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IDependencyAnalyzer(ABC):
    """Контракт анализатора. Каждый язык — свой наследник.

    Анализатор извлекает СЫРЫЕ зависимости (как они записаны в коде).
    Разрешением в реальные пути занимается DependencyGraph."""

    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Множество расширений, которые обрабатывает анализатор."""
        raise NotImplementedError

    @abstractmethod
    def extract_dependencies(self, file_path: str, source: str) -> list[str]:
        """Извлекает сырые имена зависимостей из исходника.

        Args:
            file_path: абсолютный путь к файлу (для контекста/логов).
            source:    содержимое файла.

        Returns:
            C++:    ['core/engine.h', 'utils.h']   (только "..."-include)
            Python: ['mypkg.utils', 'os']          (модули как в import)
        """
        raise NotImplementedError