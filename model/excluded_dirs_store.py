"""Персистентное хранилище исключённых папок по проектам.

Ключ — абсолютный путь корня проекта; значение — список
относительных путей исключённых папок. Формат: JSON."""
from __future__ import annotations

import json
import os


class ExcludedDirsStore:
    """Хранит наборы исключённых папок для разных проектов."""

    def __init__(self, storage_path: str) -> None:
        self._storage_path = storage_path
        # abs_root -> set(rel_dir)
        self._data: dict[str, set[str]] = {}
        self.load()

    # ------------------------------------------------------------------
    def get(self, root_path: str) -> set[str]:
        return set(self._data.get(self._key(root_path), set()))

    def set(self, root_path: str, rel_dirs: set[str]) -> None:
        key = self._key(root_path)
        if rel_dirs:
            self._data[key] = set(rel_dirs)
        else:
            self._data.pop(key, None)   # пусто -> не храним
        self.save()

    # ------------------------------------------------------------------
    def load(self) -> None:
        if not os.path.isfile(self._storage_path):
            self._data = {}
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError):
            self._data = {}
            return
        if not isinstance(raw, dict):
            self._data = {}
            return
        result: dict[str, set[str]] = {}
        for key, dirs in raw.items():
            if isinstance(dirs, list):
                result[key] = {
                    str(d).replace("\\", "/").strip("/")
                    for d in dirs if isinstance(d, str) and d.strip()
                }
        self._data = result

    def save(self) -> None:
        try:
            os.makedirs(
                os.path.dirname(os.path.abspath(self._storage_path)),
                exist_ok=True,
            )
            serializable = {
                k: sorted(v) for k, v in self._data.items()
            }
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except OSError:
            pass   # не мешаем работе приложения

    # ------------------------------------------------------------------
    @staticmethod
    def _key(root_path: str) -> str:
        return os.path.normcase(os.path.abspath(root_path))