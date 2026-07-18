"""Тесты read_text: перебор кодировок и обработка битых байтов."""
from model.file_reader import read_text


def test_read_utf8(tmp_path):
    f = tmp_path / "u.txt"
    f.write_text("привет мир", encoding="utf-8")
    assert read_text(str(f)) == "привет мир"


def test_read_utf8_bom(tmp_path):
    f = tmp_path / "b.txt"
    f.write_text("hello", encoding="utf-8-sig")
    # BOM не должен ломать чтение
    assert "hello" in read_text(str(f))


def test_read_cp1251(tmp_path):
    f = tmp_path / "c.txt"
    f.write_bytes("Привет".encode("cp1251"))
    result = read_text(str(f))
    # Должно прочитаться (какой-то кодировкой из списка) без исключений
    assert isinstance(result, str)
    assert len(result) > 0


def test_read_broken_bytes_no_crash(tmp_path):
    f = tmp_path / "broken.txt"
    # Заведомо некорректная utf-8 последовательность
    f.write_bytes(b"\xff\xfe\x00\x01valid")
    # errors='replace' в финале не должен падать
    result = read_text(str(f))
    assert isinstance(result, str)


def test_read_empty_file(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    assert read_text(str(f)) == ""