"""Тесты MainPresenter с фейковым View (без Tkinter)."""
import os

import pytest

from model.app_model import AppModel
from presenter.main_presenter import MainPresenter
from view.iview import IView
from model.file_node import FileNode


class FakeView(IView):
    """Минимальный фейк View: записывает вызовы, отдаёт заготовки."""

    def __init__(self):
        self.callbacks = {}
        self.status_messages = []
        self.errors = []
        self.tree_shown = None
        self.preview_text = ""
        self.selected_paths = []
        self.token_count = None
        self.token_limit_value = 0
        self.max_depth = 1
        self.options = {"strip_comments": False, "strip_blank": False}
        self.history_shown = None
        self.extensions_shown = None
        self.clipboard = None
        self.save_path_to_return = None
        self.saved = None
        self.excluded_shown = None

    # --- регистрация колбэков ---
    def set_on_choose_folder(self, cb): self.callbacks["choose"] = cb
    def set_on_resolve_deps(self, cb): self.callbacks["resolve"] = cb
    def set_on_build(self, cb): self.callbacks["build"] = cb
    def set_on_copy(self, cb): self.callbacks["copy"] = cb
    def set_on_history_open(self, cb): self.callbacks["history"] = cb
    def set_on_extensions_changed(self, cb): self.callbacks["ext"] = cb
    def set_on_save_to_file(self, cb): self.callbacks["save"] = cb

    # --- дерево ---
    def show_tree(self, root_node): self.tree_shown = root_node
    def get_selected_paths(self): return list(self.selected_paths)
    def set_selected_paths(self, rel_paths):
        self.selected_paths = list(rel_paths)

    # --- параметры ---
    def get_max_depth(self): return self.max_depth
    def get_token_limit(self): return self.token_limit_value
    def set_token_limit(self, limit): self.token_limit_value = limit
    def get_options(self): return dict(self.options)

    # --- вывод ---
    def show_preview(self, text): self.preview_text = text
    def get_preview_text(self): return self.preview_text
    def show_token_count(self, count, limit, exact):
        self.token_count = (count, limit, exact)
    def show_status(self, message): self.status_messages.append(message)
    def show_error(self, message): self.errors.append(message)
    def copy_to_clipboard(self, text): self.clipboard = text

    # --- история ---
    def show_history(self, folders): self.history_shown = list(folders)

    # --- расширения ---
    def show_extensions(self, all_extensions, active):
        self.extensions_shown = (list(all_extensions), set(active))

    # --- сохранение ---
    def ask_save_path(self, default_name):
        return self.save_path_to_return
    # если в твоём IView save-метод называется иначе — поправь

    def set_on_exclude_dir(self, cb): self.callbacks["exclude"] = cb
    def set_on_include_dir(self, cb): self.callbacks["include"] = cb
    def show_excluded_dirs(self, excluded):
        self.excluded_shown = list(excluded)


@pytest.fixture
def project(tmp_path):
    (tmp_path / "a.py").write_text("import b\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("x = 1\n", encoding="utf-8")
    return str(tmp_path)


@pytest.fixture
def wired(project):
    view = FakeView()
    model = AppModel()
    presenter = MainPresenter(view, model)
    return view, model, presenter, project


def test_choose_folder_shows_tree(wired):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    assert view.tree_shown is not None
    assert view.errors == []
    # статус об успешной загрузке
    assert any("загружен" in s.lower() for s in view.status_messages)


def test_choose_folder_bad_path(wired):
    view, model, presenter, project = wired
    view.callbacks["choose"]("/no/such/folder/xyz")
    assert view.errors   # ошибка показана


def test_resolve_deps_no_selection(wired):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    view.selected_paths = []
    view.callbacks["resolve"]()
    assert view.errors   # "не выбран файл"


def test_resolve_deps_pulls_dependencies(wired):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    view.selected_paths = ["a.py"]
    view.max_depth = 1
    view.callbacks["resolve"]()
    # a.py импортирует b -> b.py подтянулся
    assert "b.py" in view.selected_paths


def test_build_no_selection(wired):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    view.selected_paths = []
    view.callbacks["build"]()
    assert view.errors


def test_build_produces_preview(wired):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    view.selected_paths = ["a.py"]
    view.callbacks["build"]()
    assert "import b" in view.preview_text
    assert view.token_count is not None


def test_copy_nothing(wired):
    view, model, presenter, project = wired
    view.preview_text = ""
    view.callbacks["copy"]()
    assert view.errors   # нечего копировать


def test_copy_after_build(wired):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    view.selected_paths = ["a.py"]
    view.callbacks["build"]()
    view.callbacks["copy"]()
    assert view.clipboard is not None
    assert "import b" in view.clipboard


def test_extensions_changed_rescans(wired):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    # оставим только .py (уже активно) — дерево перерисуется без ошибок
    view.callbacks["ext"]({".py"})
    assert view.tree_shown is not None
    assert view.errors == []


def test_save_to_file_nothing(wired):
    view, model, presenter, project = wired
    view.preview_text = ""
    view.callbacks["save"]()
    assert view.errors   # нечего сохранять


def test_save_to_file_cancelled(wired, tmp_path):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    view.selected_paths = ["a.py"]
    view.callbacks["build"]()
    view.save_path_to_return = None   # пользователь отменил
    view.callbacks["save"]()
    assert any("отмен" in s.lower() for s in view.status_messages)


def test_save_to_file_success(wired, tmp_path):
    view, model, presenter, project = wired
    view.callbacks["choose"](project)
    view.selected_paths = ["a.py"]
    view.callbacks["build"]()
    out = str(tmp_path / "saved.txt")
    view.save_path_to_return = out
    view.callbacks["save"]()
    assert os.path.isfile(out)
    assert "import b" in open(out, encoding="utf-8").read()


def test_history_shown_on_start(wired):
    view, model, presenter, project = wired
    # При инициализации Presenter показывает историю
    assert view.history_shown is not None