"""Тесты CppAnalyzer: извлечение #include "..."."""
from model.analyzers.cpp_analyzer import CppAnalyzer


def test_quoted_includes_extracted():
    a = CppAnalyzer()
    src = '#include "core/engine.h"\n#include "utils.h"\n'
    deps = a.extract_dependencies("x.cpp", src)
    assert deps == ["core/engine.h", "utils.h"]


def test_system_includes_ignored():
    a = CppAnalyzer()
    src = '#include <vector>\n#include "local.h"\n'
    deps = a.extract_dependencies("x.cpp", src)
    assert deps == ["local.h"]
    assert "<vector>" not in deps


def test_includes_in_comments_ignored():
    a = CppAnalyzer()
    src = (
        '// #include "commented.h"\n'
        '/* #include "block.h" */\n'
        '#include "real.h"\n'
    )
    deps = a.extract_dependencies("x.cpp", src)
    assert deps == ["real.h"]


def test_backslashes_normalized():
    a = CppAnalyzer()
    # raw-строка: r"\d" == реальный "\d", здесь один backslash-разделитель.
    src = r'#include "sub\dir\file.h"' + "\n"
    deps = a.extract_dependencies("x.cpp", src)
    assert deps == ["sub/dir/file.h"]


def test_spaces_after_hash():
    a = CppAnalyzer()
    src = '#   include   "spaced.h"\n'
    deps = a.extract_dependencies("x.cpp", src)
    assert deps == ["spaced.h"]


def test_supported_extensions():
    a = CppAnalyzer()
    exts = a.supported_extensions()
    assert ".cpp" in exts and ".h" in exts


def test_empty_source():
    a = CppAnalyzer()
    assert a.extract_dependencies("x.cpp", "") == []