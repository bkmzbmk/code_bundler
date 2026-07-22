"""Тесты IgnoreRules: встроенные паттерны + связка с .gitignore."""
from model.ignore_rules import IgnoreRules
from model.gitignore_rules import GitignoreRules


def test_builtin_exact_name():
    rules = IgnoreRules({"build", "__pycache__"})
    assert rules.is_ignored("/proj/build") is True
    assert rules.is_ignored("/proj/src/__pycache__") is True
    assert rules.is_ignored("/proj/src") is False


def test_builtin_glob():
    rules = IgnoreRules({"cmake-build-*"})
    assert rules.is_ignored("/proj/cmake-build-debug") is True
    assert rules.is_ignored("/proj/cmake-build-release") is True
    assert rules.is_ignored("/proj/build") is False


def test_add_pattern():
    rules = IgnoreRules(set())
    rules.add("secret")
    assert rules.is_ignored("/proj/secret") is True


def test_gitignore_integration():
    rules = IgnoreRules(set())
    gi = GitignoreRules()
    gi.load_lines(["*.log", "build/"])
    rules.set_gitignore(gi)

    assert rules.is_ignored_rel("/p/app.log", "app.log", False) is True
    assert rules.is_ignored_rel("/p/build", "build", True) is True
    assert rules.is_ignored_rel("/p/main.py", "main.py", False) is False


def test_has_gitignore():
    rules = IgnoreRules(set())
    assert rules.has_gitignore() is False
    gi = GitignoreRules()
    gi.load_lines(["*.tmp"])
    rules.set_gitignore(gi)
    assert rules.has_gitignore() is True


def test_set_gitignore_none():
    rules = IgnoreRules(set())
    rules.set_gitignore(None)
    assert rules.has_gitignore() is False


def test_is_ignored_rel_builtin_priority():
    # встроенный паттерн срабатывает даже без gitignore
    rules = IgnoreRules({".git"})
    assert rules.is_ignored_rel("/p/.git", ".git", True) is True

def test_excluded_dir_and_content():
    rules = IgnoreRules(set())
    rules.set_excluded_dirs({"src/tests"})
    # сама папка
    assert rules.is_ignored_rel("/p/src/tests", "src/tests", True) is True
    # содержимое
    assert rules.is_ignored_rel(
        "/p/src/tests/t.py", "src/tests/t.py", False
    ) is True
    # соседняя папка не задета
    assert rules.is_ignored_rel("/p/src/app", "src/app", True) is False


def test_add_remove_excluded_dir():
    rules = IgnoreRules(set())
    rules.add_excluded_dir("build2")
    assert "build2" in rules.get_excluded_dirs()
    rules.remove_excluded_dir("build2")
    assert "build2" not in rules.get_excluded_dirs()


def test_excluded_dir_normalizes_separators():
    rules = IgnoreRules(set())
    rules.add_excluded_dir("a\\b\\")   # backslash + хвостовой слэш
    assert rules.is_ignored_rel("/p/a/b", "a/b", True) is True