"""Тесты PythonAnalyzer: import / from ... import."""
from model.analyzers.python_analyzer import PythonAnalyzer


def test_plain_import():
    a = PythonAnalyzer()
    deps = a.extract_dependencies("x.py", "import os\nimport sys\n")
    assert "os" in deps and "sys" in deps


def test_dotted_import():
    a = PythonAnalyzer()
    deps = a.extract_dependencies("x.py", "import mypkg.utils\n")
    assert "mypkg.utils" in deps


def test_from_import():
    a = PythonAnalyzer()
    deps = a.extract_dependencies("x.py", "from mypkg import helpers\n")
    assert "mypkg" in deps


def test_relative_import_single_dot():
    a = PythonAnalyzer()
    deps = a.extract_dependencies("x.py", "from . import sibling\n")
    assert ".sibling" in deps


def test_relative_import_double_dot():
    a = PythonAnalyzer()
    deps = a.extract_dependencies("x.py", "from ..core import engine\n")
    assert "..core" in deps


def test_multiple_names_import():
    a = PythonAnalyzer()
    deps = a.extract_dependencies("x.py", "import a.b.c, d\n")
    assert "a.b.c" in deps and "d" in deps


def test_regex_fallback_on_syntax_error():
    a = PythonAnalyzer()
    # Битый синтаксис -> ast упадёт, сработает regex-fallback
    src = "import os\ndef (((broken\nfrom pkg import x\n"
    deps = a.extract_dependencies("x.py", src)
    assert "os" in deps
    assert "pkg" in deps


def test_supported_extensions():
    a = PythonAnalyzer()
    assert ".py" in a.supported_extensions()


def test_empty_source():
    a = PythonAnalyzer()
    assert a.extract_dependencies("x.py", "") == []