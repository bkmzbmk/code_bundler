"""Реализация IView на Tkinter. Только виджеты и их обновление.
Никакой бизнес-логики."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable

from model.file_node import FileNode
from view.iview import IView

CHECKED = "☑"
UNCHECKED = "☐"


class MainView(tk.Frame, IView):
    """Главное окно: дерево файлов + параметры + предпросмотр."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        # Колбэки (Presenter подставит свои)
        self._on_choose_folder: Callable[[str], None] | None = None
        self._on_resolve_deps: Callable[[], None] | None = None
        self._on_build: Callable[[], None] | None = None
        self._on_copy: Callable[[], None] | None = None

        # item_id -> FileNode
        self._node_by_item: dict[str, FileNode] = {}
        # item_id -> checked(bool)
        self._checked: dict[str, bool] = {}

        # Последний подсчёт токенов (для перерисовки при смене лимита)
        self._last_token_count: int | None = None
        self._last_token_exact: bool = False

        self._build_widgets()

    # ==================================================================
    # Построение интерфейса
    # ==================================================================
    def _build_widgets(self) -> None:
        # --- Верхняя панель: выбор папки ---
        top = tk.Frame(self)
        top.pack(fill="x", padx=5, pady=5)

        tk.Button(top, text="Выбрать папку",
                  command=self._choose_folder_clicked).pack(side="left")
        self._folder_label = tk.Label(top, text="(папка не выбрана)",
                                      anchor="w")
        self._folder_label.pack(side="left", padx=10, fill="x", expand=True)

        # --- Основная область: слева дерево, справа предпросмотр ---
        paned = tk.PanedWindow(self, orient="horizontal", sashwidth=5)
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        # === Левая панель ===
        left = tk.Frame(paned)
        paned.add(left, minsize=250)

        tk.Label(left, text="Файлы проекта "
                            "(клик — отметить/снять):").pack(anchor="w")

        tree_frame = tk.Frame(left)
        tree_frame.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(tree_frame, show="tree", selectmode="none")
        scroll = ttk.Scrollbar(tree_frame, orient="vertical",
                               command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._tree.bind("<Button-1>", self._on_tree_click)

        # === Правая панель ===
        right = tk.Frame(paned)
        paned.add(right, minsize=300)

        # Параметры
        params = tk.LabelFrame(right, text="Параметры")
        params.pack(fill="x", pady=(0, 5))

        depth_row = tk.Frame(params)
        depth_row.pack(fill="x", padx=5, pady=3)
        tk.Label(depth_row, text="Глубина зависимостей:").pack(side="left")
        self._depth_var = tk.IntVar(value=1)
        tk.Spinbox(depth_row, from_=0, to=99, width=5,
                   textvariable=self._depth_var).pack(side="left", padx=5)
        tk.Label(depth_row, text="(0 = без зависимостей)").pack(side="left")

        self._strip_comments_var = tk.BooleanVar(value=False)
        self._strip_blank_var = tk.BooleanVar(value=False)
        tk.Checkbutton(params, text="Удалять комментарии",
                       variable=self._strip_comments_var).pack(anchor="w",
                                                               padx=5)
        tk.Checkbutton(params, text="Удалять пустые строки",
                       variable=self._strip_blank_var).pack(anchor="w",
                                                            padx=5)

        # Лимит токенов
        limit_row = tk.Frame(params)
        limit_row.pack(fill="x", padx=5, pady=3)
        tk.Label(limit_row, text="Лимит токенов:").pack(side="left")
        self._token_limit_var = tk.IntVar(value=0)
        limit_spin = tk.Spinbox(
            limit_row, from_=0, to=100_000_000, increment=1000,
            width=12, textvariable=self._token_limit_var,
        )
        limit_spin.pack(side="left", padx=5)
        # При изменении лимита — пересчитать индикатор превышения
        self._token_limit_var.trace_add("write", self._on_token_limit_changed)

        # Кнопки действий
        actions = tk.Frame(right)
        actions.pack(fill="x", pady=(0, 5))
        tk.Button(actions, text="Подтянуть зависимости",
                  command=self._resolve_clicked).pack(side="left")
        tk.Button(actions, text="Собрать",
                  command=self._build_clicked).pack(side="left", padx=5)
        tk.Button(actions, text="Копировать",
                  command=self._copy_clicked).pack(side="left")

        # Счётчик токенов
        self._token_label = tk.Label(right, text="Токенов: —", anchor="w")
        self._token_label.pack(fill="x")

        # Предпросмотр
        tk.Label(right, text="Предпросмотр:").pack(anchor="w")
        preview_frame = tk.Frame(right)
        preview_frame.pack(fill="both", expand=True)
        self._preview = tk.Text(preview_frame, wrap="none", height=10)
        pv_scroll_y = ttk.Scrollbar(preview_frame, orient="vertical",
                                    command=self._preview.yview)
        pv_scroll_x = ttk.Scrollbar(right, orient="horizontal",
                                    command=self._preview.xview)
        self._preview.configure(yscrollcommand=pv_scroll_y.set,
                                xscrollcommand=pv_scroll_x.set)
        self._preview.pack(side="left", fill="both", expand=True)
        pv_scroll_y.pack(side="right", fill="y")
        pv_scroll_x.pack(fill="x")

        # Статус-бар
        self._status = tk.Label(self, text="Готово", anchor="w",
                                relief="sunken")
        self._status.pack(fill="x", side="bottom")

    # ==================================================================
    # Внутренние обработчики виджетов -> вызов колбэков Presenter
    # ==================================================================
    def _choose_folder_clicked(self) -> None:
        folder = filedialog.askdirectory(title="Выберите папку проекта")
        if folder and self._on_choose_folder:
            self._folder_label.config(text=folder)
            self._on_choose_folder(folder)

    def _resolve_clicked(self) -> None:
        if self._on_resolve_deps:
            self._on_resolve_deps()

    def _build_clicked(self) -> None:
        if self._on_build:
            self._on_build()

    def _copy_clicked(self) -> None:
        if self._on_copy:
            self._on_copy()

    def _on_tree_click(self, event: tk.Event) -> None:
        """Обработка клика по дереву.

        Клик по значку раскрытия (+/-) — пропускаем к Treeview, чтобы
        папка развернулась/свернулась штатно.
        Клик по имени/чекбоксу — переключаем отметку файла/папки.
        """
        item = self._tree.identify_row(event.y)
        if not item:
            return  # клик по пустому месту — ничего не делаем

        # Определяем, по какому элементу строки попал клик.
        # 'Treeitem.indicator' — это значок раскрытия (+/-).
        element = self._tree.identify_element(event.x, event.y)
        if "indicator" in element:
            # Пусть Treeview сам развернёт/свернёт ветку — НЕ возвращаем "break"
            return

        # Иначе — это клик по чекбоксу/имени: переключаем отметку.
        self._toggle_item(item)
        return "break"

    # ==================================================================
    # Логика чекбоксов (только визуальная часть)
    # ==================================================================
    def _toggle_item(self, item: str) -> None:
        new_state = not self._checked.get(item, False)
        self._set_item_state(item, new_state)

    def _set_item_state(self, item: str, state: bool) -> None:
        node = self._node_by_item.get(item)
        self._checked[item] = state
        self._update_item_text(item)
        # Каскад на детей (для папок)
        if node and node.is_dir:
            for child in self._tree.get_children(item):
                self._set_item_state(child, state)

    def _update_item_text(self, item: str) -> None:
        node = self._node_by_item.get(item)
        if node is None:
            return
        box = CHECKED if self._checked.get(item, False) else UNCHECKED
        self._tree.item(item, text=f"{box} {node.name}")

    # ==================================================================
    # Реализация IView
    # ==================================================================
    # --- регистрация обработчиков ---
    def set_on_choose_folder(self, callback: Callable[[str], None]) -> None:
        self._on_choose_folder = callback

    def set_on_resolve_deps(self, callback: Callable[[], None]) -> None:
        self._on_resolve_deps = callback

    def set_on_build(self, callback: Callable[[], None]) -> None:
        self._on_build = callback

    def set_on_copy(self, callback: Callable[[], None]) -> None:
        self._on_copy = callback

    # --- дерево ---
    def show_tree(self, root_node: FileNode) -> None:
        self._tree.delete(*self._tree.get_children())
        self._node_by_item.clear()
        self._checked.clear()
        # Корень не показываем, показываем его детей
        for child in root_node.children:
            self._insert_node("", child)

    def _insert_node(self, parent_item: str, node: FileNode) -> None:
        item = self._tree.insert(parent_item, "end",
                                 text=f"{UNCHECKED} {node.name}",
                                 open=False)
        self._node_by_item[item] = node
        self._checked[item] = False
        for child in node.children:
            self._insert_node(item, child)

    def get_selected_paths(self) -> list[str]:
        result: list[str] = []
        for item, node in self._node_by_item.items():
            if not node.is_dir and self._checked.get(item, False):
                result.append(node.rel_path.replace("\\", "/"))
        return result

    def set_selected_paths(self, rel_paths: list[str]) -> None:
        wanted = {p.replace("\\", "/") for p in rel_paths}
        for item, node in self._node_by_item.items():
            if node.is_dir:
                continue
            state = node.rel_path.replace("\\", "/") in wanted
            self._checked[item] = state
            self._update_item_text(item)
        # Раскрываем ветки с отмеченными файлами
        self._expand_to_selected(wanted)

    def _expand_to_selected(self, wanted: set[str]) -> None:
        for item, node in self._node_by_item.items():
            if (not node.is_dir
                    and node.rel_path.replace("\\", "/") in wanted):
                parent = self._tree.parent(item)
                while parent:
                    self._tree.item(parent, open=True)
                    parent = self._tree.parent(parent)

    # --- параметры ---
    def get_max_depth(self) -> int:
        try:
            return int(self._depth_var.get())
        except (tk.TclError, ValueError):
            return 1

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

    def get_options(self) -> dict:
        return {
            "strip_comments": self._strip_comments_var.get(),
            "strip_blank": self._strip_blank_var.get(),
        }

    # --- вывод ---
    def show_preview(self, text: str) -> None:
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", text)

    def get_preview_text(self) -> str:
        return self._preview.get("1.0", "end-1c")

    def show_token_count(self, count: int, limit: int, exact: bool) -> None:
        self._last_token_count = count
        self._last_token_exact = exact
        # Синхронизируем поле лимита, если Presenter передал другой лимит
        if limit != self._token_limit_var.get():
            self._token_limit_var.set(limit)
        self._render_token_label(count, limit, exact)

    def _render_token_label(self, count: int, limit: int,
                            exact: bool) -> None:
        mode = "точно" if exact else "оценка"
        warn = "  ⚠ ПРЕВЫШЕН ЛИМИТ" if (limit > 0 and count > limit) else ""
        self._token_label.config(
            text=f"Токенов: {count} / {limit} ({mode}){warn}",
            fg="red" if (limit > 0 and count > limit) else "black",
        )

    def show_status(self, message: str) -> None:
        self._status.config(text=message)

    def show_error(self, message: str) -> None:
        messagebox.showerror("Ошибка", message)

    def copy_to_clipboard(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)