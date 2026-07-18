"""Pytest-тесты сбора расширений и фильтра по расширениям."""
import os

from config import DEFAULT_IGNORE
from model.ignore_rules import IgnoreRules
from model.project_scanner import ProjectScanner


def _make_tree(root):
    """Создаёт файлы разных типов + игнор-папку + .gitignore."""
    (root / "src").mkdir()
    (root / "src" / "main.cpp").write_text("int main(){}", encoding="utf-8")
    (root / "src" / "util.h").write_text("#pragma once", encoding="utf-8")
    (root / "app.py").write_text("x = 1", encoding="utf-8")
    (root / "readme.md").write_text("# hi", encoding="utf-8")
    (root / "data.json").write_text("{}", encoding="utf-8")
    # Игнор через .gitignore
    (root / ".gitignore").write_text("*.json\nbuild/\n", encoding="utf-8")
    (root / "build").mkdir()
    (root / "build" / "obj.o").write_text("", encoding="utf-8")


def test_collect_extensions(tmp_path):
    _make_tree(tmp_path)
    ignore = IgnoreRules(set(DEFAULT_IGNORE))
    scanner = ProjectScanner(ignore, None, use_gitignore=True)

    exts = scanner.collect_extensions(str(tmp_path))
    # .json игнорируется (.gitignore), .o в build/ игнорируется
    assert ".cpp" in exts
    assert ".h" in exts
    assert ".py" in exts
    assert ".md" in exts
    assert ".json" not in exts   # исключён через .gitignore
    assert ".o" not in exts      # build/ игнорируется


def test_scan_with_filter(tmp_path):
    _make_tree(tmp_path)
    ignore = IgnoreRules(set(DEFAULT_IGNORE))
    scanner = ProjectScanner(ignore, {".py"}, use_gitignore=True)

    root = scanner.scan(str(tmp_path))
    files = [n.rel_path for n in root.iter_files()]
    # Только .py файлы попадают в дерево
    assert "app.py" in files
    assert all(f.endswith(".py") for f in files)


def test_set_extensions_rescan(tmp_path):
    _make_tree(tmp_path)
    ignore = IgnoreRules(set(DEFAULT_IGNORE))
    scanner = ProjectScanner(ignore, {".py"}, use_gitignore=True)

    root1 = scanner.scan(str(tmp_path))
    assert [n.rel_path for n in root1.iter_files()] == ["app.py"]

    scanner.set_extensions({".cpp", ".h"})
    root2 = scanner.scan(str(tmp_path))
    files = sorted(n.rel_path for n in root2.iter_files())
    assert files == ["src/main.cpp", "src/util.h"]