"""Тесты FileNode: построение, обходы, поиск."""
from model.file_node import FileNode


def _tree() -> FileNode:
    root = FileNode("/proj", "", is_dir=True)
    src = FileNode("/proj/src", "src", is_dir=True)
    main = FileNode("/proj/src/main.py", "src/main.py", is_dir=False)
    util = FileNode("/proj/util.py", "util.py", is_dir=False)
    root.add_child(src)
    src.add_child(main)
    root.add_child(util)
    return root


def test_add_child_sets_parent():
    root = FileNode("/p", "", is_dir=True)
    child = FileNode("/p/a.py", "a.py", is_dir=False)
    root.add_child(child)
    assert child.parent is root
    assert child in root.children


def test_iter_files_only_files():
    root = _tree()
    files = sorted(n.rel_path for n in root.iter_files())
    assert files == ["src/main.py", "util.py"]


def test_iter_all_includes_dirs():
    root = _tree()
    rels = sorted(n.rel_path for n in root.iter_all())
    assert "" in rels          # корень
    assert "src" in rels       # папка
    assert "src/main.py" in rels


def test_find_by_rel_path():
    root = _tree()
    node = root.find_by_rel_path("src/main.py")
    assert node is not None
    assert node.name == "main.py"


def test_find_by_rel_path_backslash():
    root = _tree()
    # разделители нормализуются
    node = root.find_by_rel_path("src\\main.py")
    assert node is not None


def test_find_by_rel_path_not_found():
    root = _tree()
    assert root.find_by_rel_path("missing.py") is None


def test_name_from_path():
    node = FileNode("/a/b/file.cpp", "b/file.cpp", is_dir=False)
    assert node.name == "file.cpp"