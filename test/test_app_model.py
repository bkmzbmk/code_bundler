"""Интеграционные тесты AppModel (фасад Model)."""
import os
import re

import pytest

from model.app_model import AppModel


@pytest.fixture
def sample_project(tmp_path):
    """Небольшой проект: C++ цепочка + Python + мусорные файлы."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.cpp").write_text(
        '#include "engine.h"\nint main(){}\n', encoding="utf-8"
    )
    (tmp_path / "src" / "engine.h").write_text(
        "#pragma once\n", encoding="utf-8"
    )
    (tmp_path / "app.py").write_text("import os\n", encoding="utf-8")
    (tmp_path / "readme.md").write_text("# doc\n", encoding="utf-8")
    (tmp_path / "data.json").write_text("{}\n", encoding="utf-8")
    return tmp_path


def test_load_project_returns_tree(sample_project):
    m = AppModel()
    root = m.load_project(str(sample_project))
    files = {n.rel_path for n in root.iter_files()}
    # По умолчанию активны только code-расширения (.cpp/.h/.py/...)
    assert "src/main.cpp" in files
    assert "app.py" in files
    # .md и .json НЕ входят в дефолтные активные расширения
    assert "readme.md" not in files
    assert "data.json" not in files


def test_get_root_path_and_node(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    assert m.get_root_path() == os.path.abspath(str(sample_project))
    assert m.get_root_node() is not None


def test_all_extensions_collected(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    all_ext = m.get_all_extensions()
    # Собрались все реальные расширения + дефолтные
    assert ".md" in all_ext
    assert ".json" in all_ext
    assert ".cpp" in all_ext


def test_active_extensions_default(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    active = m.get_active_extensions()
    assert ".cpp" in active
    assert ".md" not in active   # md не в дефолтных


def test_set_active_extensions_rescans(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    # Включаем .md — дерево должно пересканироваться
    root = m.set_active_extensions({".md"})
    assert root is not None
    files = {n.rel_path for n in root.iter_files()}
    assert "readme.md" in files
    assert "app.py" not in files   # .py больше не активен


def test_set_active_extensions_no_project():
    m = AppModel()
    # Проект не загружен -> None
    assert m.set_active_extensions({".py"}) is None


def test_resolve_dependencies(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    resolved = m.resolve_dependencies(["src/main.cpp"], max_depth=1)
    # main.cpp тянет engine.h
    assert "src/main.cpp" in resolved
    assert "src/engine.h" in resolved


def test_resolve_dependencies_depth_0(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    resolved = m.resolve_dependencies(["src/main.cpp"], max_depth=0)
    assert resolved == ["src/main.cpp"]


def test_resolve_no_project():
    m = AppModel()
    # Без проекта возвращает исходный список
    assert m.resolve_dependencies(["a.py"], 1) == ["a.py"]


def test_get_dependency_edges(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    m.resolve_dependencies(["src/main.cpp"], max_depth=1)
    edges = m.get_dependency_edges()
    assert "src/main.cpp" in edges
    assert "src/engine.h" in edges["src/main.cpp"]


def test_build_bundle(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    bundle = m.build_bundle(["app.py"])
    assert "import os" in bundle
    assert "app.py" in bundle   # метка с rel_path


def test_build_bundle_no_project():
    m = AppModel()
    with pytest.raises(RuntimeError):
        m.build_bundle(["a.py"])


def test_count_tokens(sample_project):
    m = AppModel()
    assert m.count_tokens("") == 0
    assert m.count_tokens("hello world") > 0


def test_suggest_filename(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    name = m.suggest_filename()
    base = os.path.basename(str(sample_project))
    assert name.startswith(base + "_")
    assert name.endswith(".txt")
    assert re.search(r"_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.txt$", name)


def test_save_to_file(sample_project, tmp_path):
    m = AppModel()
    out = tmp_path / "result.txt"
    m.save_to_file(str(out), "content")
    assert out.read_text(encoding="utf-8") == "content"


def test_history_updated_on_load(sample_project):
    m = AppModel()
    m.load_project(str(sample_project))
    history = m.get_folder_history()
    assert os.path.abspath(str(sample_project)) in [
        os.path.abspath(p) for p in history
    ]