"""Интерфейс View. Presenter работает ТОЛЬКО через эти методы,
не зная про Tkinter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from tqdm import tk

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

    def _on_token_limit_changed(self, *_args) -> None:
        """Пользователь поменял лимит — перерисуем индикатор,
        если есть последний подсчёт токенов."""
        if self._last_token_count is None:
            return
        try:
            limit = int(self._token_limit_var.get())
        except (tk.TclError, ValueError):
            return
        self._render_token_label(
            self._last_token_count, limit, self._last_token_exact
        )

    def get_token_limit(self) -> int:
        try:
            return int(self._token_limit_var.get())
        except (tk.TclError, ValueError):
            return 0

    def set_token_limit(self, limit: int) -> None:
        self._token_limit_var.set(limit)

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