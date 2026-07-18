"""Pytest-тесты FolderHistory (persistence + порядок + дубликаты)."""
import os

from model.folder_history import FolderHistory


def test_add_and_order(tmp_path):
    store = str(tmp_path / "hist.json")
    h = FolderHistory(store, max_items=10)

    a = str(tmp_path / "a")
    b = str(tmp_path / "b")
    os.makedirs(a)
    os.makedirs(b)

    h.add(a)
    h.add(b)
    # Свежая (b) — первой
    items = h.get_all()
    assert os.path.normcase(items[0]) == os.path.normcase(os.path.abspath(b))
    assert os.path.normcase(items[1]) == os.path.normcase(os.path.abspath(a))


def test_promote_no_duplicates(tmp_path):
    store = str(tmp_path / "hist.json")
    h = FolderHistory(store)
    a = str(tmp_path / "a")
    b = str(tmp_path / "b")

    h.add(a)
    h.add(b)
    h.add(a)   # повторное открытие a — поднять наверх, без дубля

    items = h.get_all()
    assert len(items) == 2
    assert os.path.normcase(items[0]) == os.path.normcase(os.path.abspath(a))


def test_max_items(tmp_path):
    store = str(tmp_path / "hist.json")
    h = FolderHistory(store, max_items=3)
    for i in range(5):
        h.add(str(tmp_path / f"d{i}"))
    assert len(h.get_all()) == 3
    # Последние три (d4, d3, d2) — d0/d1 вытеснены
    tops = [os.path.basename(p) for p in h.get_all()]
    assert tops == ["d4", "d3", "d2"]


def test_persistence(tmp_path):
    store = str(tmp_path / "hist.json")
    a = str(tmp_path / "a")
    b = str(tmp_path / "b")

    h1 = FolderHistory(store)
    h1.add(a)
    h1.add(b)

    # Новый экземпляр читает тот же файл
    h2 = FolderHistory(store)
    items = h2.get_all()
    assert len(items) == 2
    assert os.path.normcase(items[0]) == os.path.normcase(os.path.abspath(b))


def test_remove(tmp_path):
    store = str(tmp_path / "hist.json")
    h = FolderHistory(store)
    a = str(tmp_path / "a")
    b = str(tmp_path / "b")
    h.add(a)
    h.add(b)
    h.remove(a)
    items = [os.path.basename(p) for p in h.get_all()]
    assert items == ["b"]


def test_clear(tmp_path):
    store = str(tmp_path / "hist.json")
    h = FolderHistory(store)
    h.add(str(tmp_path / "a"))
    h.clear()
    assert h.is_empty()