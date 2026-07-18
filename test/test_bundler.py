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