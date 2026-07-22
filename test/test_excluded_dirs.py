"""Тесты исключения папок через AppModel + персистентность."""
from model.app_model import AppModel
from model.excluded_dirs_store import ExcludedDirsStore


def _make_project(root):
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_a.py").write_text("y = 2\n", encoding="utf-8")
    (root / "tests" / "sub").mkdir()
    (root / "tests" / "sub" / "test_b.py").write_text(
        "z = 3\n", encoding="utf-8"
    )


def test_exclude_dir_removes_files(tmp_path):
    _make_project(tmp_path)
    m = AppModel()
    root = m.load_project(str(tmp_path))
    files = {n.rel_path for n in root.iter_files()}
    assert "tests/test_a.py" in files

    root = m.exclude_dir("tests")
    files = {n.rel_path for n in root.iter_files()}
    # Вся папка tests (включая вложенную sub) исчезла
    assert "tests/test_a.py" not in files
    assert "tests/sub/test_b.py" not in files
    assert "src/main.py" in files   # остальное на месте


def test_include_dir_restores_files(tmp_path):
    _make_project(tmp_path)
    m = AppModel()
    m.load_project(str(tmp_path))
    m.exclude_dir("tests")

    root = m.include_dir("tests")
    files = {n.rel_path for n in root.iter_files()}
    # Папка вернулась целиком
    assert "tests/test_a.py" in files
    assert "tests/sub/test_b.py" in files


def test_get_excluded_dirs(tmp_path):
    _make_project(tmp_path)
    m = AppModel()
    m.load_project(str(tmp_path))
    assert m.get_excluded_dirs() == []

    m.exclude_dir("tests")
    m.exclude_dir("src")
    # Отсортированный список
    assert m.get_excluded_dirs() == ["src", "tests"]


def test_exclude_dir_no_project():
    m = AppModel()
    # Без проекта -> None, не падаем
    assert m.exclude_dir("tests") is None


def test_excluded_dirs_affect_dependencies(tmp_path):
    """Исключённая папка не участвует в разрешении зависимостей."""
    (tmp_path / "main.py").write_text(
        "import helper\n", encoding="utf-8"
    )
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "helper.py").write_text(
        "x = 1\n", encoding="utf-8"
    )
    m = AppModel()
    m.load_project(str(tmp_path))

    # До исключения helper.py резолвится (лежит в vendor/)
    # Импорт "import helper" ищется от корня -> НЕ найдётся,
    # т.к. helper лежит в vendor. Проверяем именно исчезновение
    # файла из дерева/графа после исключения.
    m.exclude_dir("vendor")
    resolved = m.resolve_dependencies(["main.py"], max_depth=-1)
    assert "vendor/helper.py" not in resolved
    assert "main.py" in resolved


# ------------------------------------------------------------------
# Персистентность ExcludedDirsStore
# ------------------------------------------------------------------
def test_store_persistence(tmp_path):
    store_file = str(tmp_path / "excl.json")
    root = str(tmp_path / "proj")

    s1 = ExcludedDirsStore(store_file)
    s1.set(root, {"tests", "build"})

    # Новый экземпляр читает тот же файл
    s2 = ExcludedDirsStore(store_file)
    assert s2.get(root) == {"tests", "build"}


def test_store_empty_removes_key(tmp_path):
    store_file = str(tmp_path / "excl.json")
    root = str(tmp_path / "proj")

    s = ExcludedDirsStore(store_file)
    s.set(root, {"tests"})
    s.set(root, set())   # пусто -> ключ удаляется
    assert s.get(root) == set()


def test_store_per_project_isolation(tmp_path):
    store_file = str(tmp_path / "excl.json")
    proj_a = str(tmp_path / "a")
    proj_b = str(tmp_path / "b")

    s = ExcludedDirsStore(store_file)
    s.set(proj_a, {"tests"})
    s.set(proj_b, {"vendor"})

    assert s.get(proj_a) == {"tests"}
    assert s.get(proj_b) == {"vendor"}


def test_store_invalid_json(tmp_path):
    store_file = tmp_path / "bad.json"
    store_file.write_text("{ broken ]", encoding="utf-8")
    s = ExcludedDirsStore(str(store_file))
    # Битый файл -> пусто, без исключений
    assert s.get(str(tmp_path / "any")) == set()


def test_store_missing_file(tmp_path):
    s = ExcludedDirsStore(str(tmp_path / "absent.json"))
    assert s.get(str(tmp_path)) == set()