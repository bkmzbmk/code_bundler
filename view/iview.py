"""Интерфейс View. Presenter работает ТОЛЬКО через эти методы,
не зная про Tkinter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from model.file_node import FileNode


class IView(ABC):
    """Контракт между Presenter и View."""

    # --- Регистрация обработчиков (Presenter подписывается) ---
    @abstractmethod
    def set_on_choose_folder(self, callback: Callable[[str], None]) -> None:
        """callback(folder_path)."""
        raise NotImplementedError

    @abstractmethod
    def set_on_resolve_deps(self, callback: Callable[[], None]) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_on_build(self, callback: Callable[[], None]) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_on_copy(self, callback: Callable[[], None]) -> None:
        raise NotImplementedError

    # --- Дерево файлов ---
    @abstractmethod
    def show_tree(self, root_node: FileNode) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_selected_paths(self) -> list[str]:
        """Относительные пути отмеченных файлов."""
        raise NotImplementedError

    @abstractmethod
    def set_selected_paths(self, rel_paths: list[str]) -> None:
        """Отметить указанные файлы (снять отметки с остальных)."""
        raise NotImplementedError

    # --- Параметры ---
    @abstractmethod
    def get_max_depth(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_token_limit(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def set_token_limit(self, limit: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_options(self) -> dict:
        """{'strip_comments': bool, 'strip_blank': bool}."""
        raise NotImplementedError

    # --- Вывод ---
    @abstractmethod
    def show_preview(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_preview_text(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def show_token_count(self, count: int, limit: int, exact: bool) -> None:
        raise NotImplementedError

    @abstractmethod
    def show_status(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def show_error(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def copy_to_clipboard(self, text: str) -> None:
        raise NotImplementedError

    # --- История папок ---
    @abstractmethod
    def set_on_history_open(self, callback: Callable[[str], None]) -> None:
        """callback(folder_path) — двойной клик по строке истории."""
        raise NotImplementedError

    @abstractmethod
    def show_history(self, folders: list[str]) -> None:
        """Отобразить список недавних папок (свежая — первой)."""
        raise NotImplementedError

    # --- Расширения файлов ---
    @abstractmethod
    def set_on_extensions_changed(
        self, callback: Callable[[set[str]], None]
    ) -> None:
        """callback(active_extensions) — пользователь изменил набор."""
        raise NotImplementedError

    @abstractmethod
    def show_extensions(
        self, all_extensions: list[str], active: set[str]
    ) -> None:
        """Показать список расширений с отметками active."""
        raise NotImplementedError

    @abstractmethod
    def set_on_save_to_file(self, callback: Callable[[], None]) -> None:
        raise NotImplementedError

    @abstractmethod
    def ask_save_path(self, default_name: str) -> str | None:
        """Диалог выбора файла для сохранения.

        Returns:
            Выбранный путь или None, если пользователь отменил.
        """
        raise NotImplementedError