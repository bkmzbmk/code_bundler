"""Тесты DependencyGraph: разрешение зависимостей + BFS по глубине."""
import os

from config import DEFAULT_IGNORE
from model.ignore_rules import IgnoreRules
from model.project_scanner import ProjectScanner
from model.dependency_graph import DependencyGraph
from model.analyzers.analyzer_registry import AnalyzerRegistry
from model.analyzers.cpp_analyzer import CppAnalyzer
from model.analyzers.python_analyzer import PythonAnalyzer


def _registry() -> AnalyzerRegistry:
    r = AnalyzerRegistry()
    r.register(CppAnalyzer())
    r.register(PythonAnalyzer())
    return r


def _scan(root) -> object:
    ignore = IgnoreRules(set(DEFAULT_IGNORE))
    scanner = ProjectScanner(ignore, {".cpp", ".h", ".py"},
                             use_gitignore=False)
    return scanner.scan(str(root))


def _make_cpp_project(root):
    (root / "a.cpp").write_text('#include "b.h"\n', encoding="utf-8")
    (root / "b.h").write_text('#include "c.h"\n', encoding="utf-8")
    (root / "c.h").write_text("// leaf\n", encoding="utf-8")


def test_cpp_resolve_depth_0(tmp_path):
    _make_cpp_project(tmp_path)
    graph = DependencyGraph(_scan(tmp_path), _registry())
    start = [str(tmp_path / "a.cpp")]
    resolved = graph.resolve(start, max_depth=0)
    # depth 0 -> только стартовый
    assert resolved == {os.path.abspath(str(tmp_path / "a.cpp"))}


def test_cpp_resolve_depth_1(tmp_path):
    _make_cpp_project(tmp_path)
    graph = DependencyGraph(_scan(tmp_path), _registry())
    resolved = graph.resolve([str(tmp_path / "a.cpp")], max_depth=1)
    names = {os.path.basename(p) for p in resolved}
    assert names == {"a.cpp", "b.h"}   # только прямые


def test_cpp_resolve_unlimited(tmp_path):
    _make_cpp_project(tmp_path)
    graph = DependencyGraph(_scan(tmp_path), _registry())
    resolved = graph.resolve([str(tmp_path / "a.cpp")], max_depth=-1)
    names = {os.path.basename(p) for p in resolved}
    assert names == {"a.cpp", "b.h", "c.h"}   # вся цепочка


def test_cpp_include_in_subdir(tmp_path):
    (tmp_path / "core").mkdir()
    (tmp_path / "main.cpp").write_text(
        '#include "core/engine.h"\n', encoding="utf-8"
    )
    (tmp_path / "core" / "engine.h").write_text("// e\n", encoding="utf-8")
    graph = DependencyGraph(_scan(tmp_path), _registry())
    resolved = graph.resolve([str(tmp_path / "main.cpp")], max_depth=1)
    names = {os.path.basename(p) for p in resolved}
    assert "engine.h" in names


def test_cpp_missing_include_ignored(tmp_path):
    (tmp_path / "a.cpp").write_text(
        '#include "nonexistent.h"\n', encoding="utf-8"
    )
    graph = DependencyGraph(_scan(tmp_path), _registry())
    resolved = graph.resolve([str(tmp_path / "a.cpp")], max_depth=1)
    # Несуществующий include не добавляется
    assert resolved == {os.path.abspath(str(tmp_path / "a.cpp"))}


def test_python_absolute_import(tmp_path):
    (tmp_path / "main.py").write_text(
        "import helper\n", encoding="utf-8"
    )
    (tmp_path / "helper.py").write_text("x = 1\n", encoding="utf-8")
    graph = DependencyGraph(_scan(tmp_path), _registry())
    resolved = graph.resolve([str(tmp_path / "main.py")], max_depth=1)
    names = {os.path.basename(p) for p in resolved}
    assert names == {"main.py", "helper.py"}


def test_python_package_import(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mod.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "main.py").write_text(
        "from pkg import mod\n", encoding="utf-8"
    )
    graph = DependencyGraph(_scan(tmp_path), _registry())
    resolved = graph.resolve([str(tmp_path / "main.py")], max_depth=1)
    # from pkg import mod -> резолвится пакет pkg/__init__.py
    names = {os.path.basename(p) for p in resolved}
    assert "__init__.py" in names


def test_python_relative_import(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "a.py").write_text("from . import b\n", encoding="utf-8")
    (pkg / "b.py").write_text("z = 3\n", encoding="utf-8")
    graph = DependencyGraph(_scan(tmp_path), _registry())
    resolved = graph.resolve([str(pkg / "a.py")], max_depth=1)
    names = {os.path.basename(p) for p in resolved}
    assert "b.py" in names


def test_external_import_ignored(tmp_path):
    (tmp_path / "main.py").write_text(
        "import os\nimport numpy\n", encoding="utf-8"
    )
    graph = DependencyGraph(_scan(tmp_path), _registry())
    resolved = graph.resolve([str(tmp_path / "main.py")], max_depth=1)
    # Внешние (os, numpy) не в дереве -> игнор
    assert resolved == {os.path.abspath(str(tmp_path / "main.py"))}


def test_get_edges(tmp_path):
    _make_cpp_project(tmp_path)
    graph = DependencyGraph(_scan(tmp_path), _registry())
    graph.resolve([str(tmp_path / "a.cpp")], max_depth=-1)
    edges = graph.get_edges()
    a_abs = os.path.abspath(str(tmp_path / "a.cpp"))
    assert a_abs in edges
    assert any(os.path.basename(t) == "b.h" for t in edges[a_abs])