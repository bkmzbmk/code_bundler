"""Pytest-тест сборщика: метки START/END и удаление пустых строк."""
from model.bundler import Bundler


def test_blank_lines_collapsed():
    b = Bundler(strip_blank_lines=True)
    text = "a\n\n\n\nb\n"
    result = b._remove_blank_lines(text)
    assert result == "a\n\nb"  # подряд пустые схлопнуты в одну


def test_remove_comments_python():
    b = Bundler(strip_comments=True)
    src = "x = 1  # коммент\ny = 2\n"
    out = b._remove_comments(src, ".py")
    assert "#" not in out
    assert "x = 1" in out and "y = 2" in out


def test_remove_comments_cpp():
    b = Bundler(strip_comments=True)
    src = "int x; // c++\n/* block */\nint y;\n"
    out = b._remove_comments(src, ".cpp")
    assert "//" not in out and "/*" not in out
    assert "int x;" in out and "int y;" in out

"""Дополнение: сборка реальных файлов и проверка меток."""
import os

from config import FILE_START_TEMPLATE, FILE_END_TEMPLATE
from model.bundler import Bundler


def test_bundle_markers(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("print(1)\n", encoding="utf-8")
    b = Bundler()
    out = b.bundle([str(f)], str(tmp_path))

    start = FILE_START_TEMPLATE.format(path="a.py")
    end = FILE_END_TEMPLATE.format(path="a.py")
    assert start in out
    assert end in out
    assert "print(1)" in out


def test_bundle_relative_paths(tmp_path):
    sub = tmp_path / "src"
    sub.mkdir()
    f = sub / "m.py"
    f.write_text("x = 1\n", encoding="utf-8")
    b = Bundler()
    out = b.bundle([str(f)], str(tmp_path))
    # rel_path в метке использует "/"
    assert "src/m.py" in out


def test_bundle_multiple_files(tmp_path):
    (tmp_path / "a.py").write_text("a = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("b = 2\n", encoding="utf-8")
    b = Bundler()
    out = b.bundle(
        [str(tmp_path / "a.py"), str(tmp_path / "b.py")],
        str(tmp_path),
    )
    assert "a = 1" in out and "b = 2" in out
    # два блока разделены пустой строкой
    assert out.count(FILE_START_TEMPLATE.format(path="a.py")) == 1


def test_bundle_strip_comments_integration(tmp_path):
    f = tmp_path / "c.py"
    f.write_text("x = 1  # comment\n", encoding="utf-8")
    b = Bundler(strip_comments=True)
    out = b.bundle([str(f)], str(tmp_path))
    assert "comment" not in out
    assert "x = 1" in out