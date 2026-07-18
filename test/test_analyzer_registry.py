"""Тесты AnalyzerRegistry: выбор анализатора по расширению."""
from model.analyzers.analyzer_registry import AnalyzerRegistry
from model.analyzers.cpp_analyzer import CppAnalyzer
from model.analyzers.python_analyzer import PythonAnalyzer


def _registry() -> AnalyzerRegistry:
    r = AnalyzerRegistry()
    r.register(CppAnalyzer())
    r.register(PythonAnalyzer())
    return r


def test_get_for_cpp():
    r = _registry()
    assert isinstance(r.get_for("main.cpp"), CppAnalyzer)
    assert isinstance(r.get_for("header.h"), CppAnalyzer)


def test_get_for_python():
    r = _registry()
    assert isinstance(r.get_for("app.py"), PythonAnalyzer)


def test_get_for_unknown():
    r = _registry()
    assert r.get_for("readme.md") is None
    assert r.get_for("data.json") is None


def test_case_insensitive():
    r = _registry()
    assert isinstance(r.get_for("MAIN.CPP"), CppAnalyzer)
    assert isinstance(r.get_for("APP.PY"), PythonAnalyzer)


def test_has_analyzer_for():
    r = _registry()
    assert r.has_analyzer_for("a.cpp") is True
    assert r.has_analyzer_for("a.txt") is False


def test_no_extension():
    r = _registry()
    assert r.get_for("Makefile") is None