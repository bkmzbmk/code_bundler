"""Pytest-тесты формирования имени и сохранения bundle в файл."""
import os
import re

from model.app_model import AppModel


def test_suggest_filename_no_project():
    m = AppModel()
    name = m.suggest_filename()
    # Проект не загружен -> префикс 'bundle', расширение .txt
    assert name.startswith("bundle_")
    assert name.endswith(".txt")


def test_suggest_filename_with_project(tmp_path):
    proj = tmp_path / "MyProj"
    proj.mkdir()
    (proj / "a.py").write_text("x = 1", encoding="utf-8")

    m = AppModel()
    m.load_project(str(proj))
    name = m.suggest_filename()

    assert name.startswith("MyProj_")
    assert name.endswith(".txt")
    # Формат времени: MyProj_2025-01-15_19-42-07.txt
    assert re.match(r"MyProj_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.txt$", name)


def test_save_to_file(tmp_path):
    m = AppModel()
    out = tmp_path / "out.txt"
    m.save_to_file(str(out), "hello world")
    assert out.read_text(encoding="utf-8") == "hello world"


def test_save_adds_txt_extension(tmp_path):
    m = AppModel()
    out = tmp_path / "noext"
    m.save_to_file(str(out), "data")
    # Расширение .txt должно добавиться
    assert os.path.isfile(str(out) + ".txt")


def test_sanitize_filename():
    m = AppModel()
    # Недопустимые символы заменяются на "_"
    assert m._sanitize_filename('a:b*c?') == "a_b_c_"
    assert m._sanitize_filename("") == "bundle"