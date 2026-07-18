"""Pytest-тесты правил .gitignore (без файловой системы)."""
from model.gitignore_rules import GitignoreRules


def _make_rules() -> GitignoreRules:
    gi = GitignoreRules()
    gi.load_lines([
        "# комментарий",
        "build/",           # папка build где угодно
        "*.log",            # любые .log
        "/secret.txt",      # только в корне
        "temp",             # temp где угодно
        "!important.log",   # но important.log не игнорим
        "docs/*.tmp",       # .tmp внутри docs (якорь из-за /)
    ])
    return gi


def test_build_dir_ignored():
    gi = _make_rules()
    assert gi.is_ignored("build", True) is True
    assert gi.is_ignored("src/build", True) is True
    # содержимое игнорируемой папки тоже игнорируется
    assert gi.is_ignored("src/build/main.o", False) is True


def test_log_pattern():
    gi = _make_rules()
    assert gi.is_ignored("app.log", False) is True
    assert gi.is_ignored("logs/app.log", False) is True


def test_negation():
    gi = _make_rules()
    # !important.log возвращает файл из-под *.log
    assert gi.is_ignored("important.log", False) is False


def test_anchored_root_only():
    gi = _make_rules()
    assert gi.is_ignored("secret.txt", False) is True
    # якорь /: только в корне, не в подпапке
    assert gi.is_ignored("sub/secret.txt", False) is False


def test_floating_temp():
    gi = _make_rules()
    assert gi.is_ignored("temp", True) is True
    assert gi.is_ignored("a/temp/b.txt", False) is True


def test_docs_anchored_glob():
    gi = _make_rules()
    assert gi.is_ignored("docs/note.tmp", False) is True
    assert gi.is_ignored("other/note.tmp", False) is False


def test_not_ignored():
    gi = _make_rules()
    assert gi.is_ignored("main.cpp", False) is False