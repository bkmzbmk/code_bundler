"""Presenter: связывает IView и AppModel. Не знает про Tkinter."""
from __future__ import annotations

from model.app_model import AppModel
from view.iview import IView


class MainPresenter:
    """Обрабатывает действия пользователя, вызывает Model,
    обновляет View."""

    def __init__(self, view: IView, model: AppModel) -> None:
        self._view = view
        self._model = model
        self._last_bundle: str = ""
        self._bind_events()
        # Проставляем в View лимит токенов из Model
        self._view.set_token_limit(self._model.token_limit)
        # Показать историю недавних папок при запуске
        self._refresh_history()

    def _bind_events(self) -> None:
        self._view.set_on_choose_folder(self.on_choose_folder)
        self._view.set_on_resolve_deps(self.on_resolve_deps)
        self._view.set_on_build(self.on_build)
        self._view.set_on_copy(self.on_copy)
        self._view.set_on_history_open(self.on_history_open)

    # ------------------------------------------------------------------
    def on_choose_folder(self, path: str) -> None:
        try:
            self._view.show_status("Сканирую проект...")
            root = self._model.load_project(path)
            self._view.show_tree(root)
            file_count = sum(1 for _ in root.iter_files())
            self._view.show_status(
                f"Проект загружен. Файлов кода: {file_count}"
            )
            self._refresh_history()   # <-- добавлено
        except Exception as e:  # noqa: BLE001
            self._view.show_error(f"Не удалось загрузить проект:\n{e}")
            self._view.show_status("Ошибка загрузки проекта")

    # ------------------------------------------------------------------
    def on_resolve_deps(self) -> None:
        selected = self._view.get_selected_paths()
        if not selected:
            self._view.show_error("Не выбран ни один файл.")
            return
        try:
            depth = self._view.get_max_depth()
            self._view.show_status("Разрешаю зависимости...")
            resolved = self._model.resolve_dependencies(selected, depth)
            self._view.set_selected_paths(resolved)
            added = len(resolved) - len(selected)
            self._view.show_status(
                f"Файлов: {len(resolved)} "
                f"(было {len(selected)}, добавлено {max(0, added)})"
            )
        except Exception as e:  # noqa: BLE001
            self._view.show_error(f"Ошибка анализа зависимостей:\n{e}")
            self._view.show_status("Ошибка анализа")

    # ------------------------------------------------------------------
    def on_build(self) -> None:
        selected = self._view.get_selected_paths()
        if not selected:
            self._view.show_error("Не выбран ни один файл.")
            return
        try:
            opts = self._view.get_options()
            self._view.show_status("Собираю...")
            bundle = self._model.build_bundle(
                selected,
                strip_comments=opts["strip_comments"],
                strip_blank=opts["strip_blank"],
            )
            self._last_bundle = bundle
            self._view.show_preview(bundle)

            # Лимит берём из View (пользователь мог изменить)
            self._model.token_limit = self._view.get_token_limit()
            tokens = self._model.count_tokens(bundle)
            self._view.show_token_count(
                tokens,
                self._model.token_limit,
                exact=self._model.tokens_available(),
            )


            self._view.show_status(
                f"Собрано {len(selected)} файл(ов), {len(bundle)} символов"
            )
        except Exception as e:  # noqa: BLE001
            self._view.show_error(f"Ошибка сборки:\n{e}")
            self._view.show_status("Ошибка сборки")

    # ------------------------------------------------------------------
    def on_copy(self) -> None:
        text = self._last_bundle or self._view.get_preview_text()
        if not text.strip():
            self._view.show_error("Нечего копировать — сначала соберите.")
            return
        self._view.copy_to_clipboard(text)
        self._view.show_status("Скопировано в буфер обмена")

    # ------------------------------------------------------------------
    def on_history_open(self, path: str) -> None:
        """Двойной клик по истории: открыть папку и поднять её наверх."""
        import os
        if not os.path.isdir(path):
            self._view.show_error(
                f"Папка недоступна (удалена или перемещена?):\n{path}"
            )
            self._model.remove_from_history(path)
            self._refresh_history()
            return
        # Переиспользуем обычную загрузку: load_project сам поднимет
        # папку наверх истории (history.add).
        self.on_choose_folder(path)

    def _refresh_history(self) -> None:
        """Обновить список истории в View."""
        self._view.show_history(self._model.get_folder_history())