"""История открытых папок проекта.

Хранит список путей в порядке «последний использованный — первым».
Персистентность — JSON-файл. Дубликаты не создаются: повторное
добавление/открытие поднимает путь наверх списка."""
from __future__ import annotations

import json
import os


class FolderHistory:
    """Список недавних папок с сохранением в JSON.

    Инвариант: путь в списке уникален (по нормализованному виду);
    самый свежий — в начале (индекс 0)."""

    def __init__(self, storage_path: str, max_items: int = 20) -> None:
        self._storage_path = storage_path
        self._max_items = max_items
        self._items: list[str] = []   # абсолютные пути, свежий — первым
        self.load()

    # ------------------------------------------------------------------
    # Доступ
    # ------------------------------------------------------------------
    def get_all(self) -> list[str]:
        """Копия списка (свежий — первым)."""
        return list(self._items)

    def is_empty(self) -> bool:
        return not self._items

    # ------------------------------------------------------------------
    # Изменение
    # ------------------------------------------------------------------
    def add(self, path: str) -> None:
        """Добавляет путь наверх. Если уже есть — поднимает наверх.

        Пустой/некорректный путь игнорируется."""
        norm = self._normalize(path)
        if not norm:
            return

        # Удаляем существующий дубликат (сравнение без учёта регистра
        # на Windows — через normcase в _same).
        self._items = [p for p in self._items if not self._same(p, norm)]
        self._items.insert(0, norm)

        # Обрезаем до лимита
        if len(self._items) > self._max_items:
            self._items = self._items[: self._max_items]

        self.save()

    def promote(self, path: str) -> None:
        """Поднять существующий путь наверх (алиас add для наглядности)."""
        self.add(path)

    def remove(self, path: str) -> None:
        """Удалить путь из истории (если есть)."""
        norm = self._normalize(path)
        before = len(self._items)
        self._items = [p for p in self._items if not self._same(p, norm)]
        if len(self._items) != before:
            self.save()

    def clear(self) -> None:
        """Очистить историю полностью."""
        self._items = []
        self.save()

    # ------------------------------------------------------------------
    # Персистентность
    # ------------------------------------------------------------------
    def load(self) -> None:
        """Загружает историю из файла (если он есть и валиден)."""
        if not os.path.isfile(self._storage_path):
            self._items = []
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            self._items = []
            return

        items = data.get("folders", []) if isinstance(data, dict) else []
        # Нормализуем, убираем дубликаты, сохраняем порядок
        seen: list[str] = []
        for raw in items:
            if not isinstance(raw, str):
                continue
            norm = self._normalize(raw)
            if norm and not any(self._same(norm, s) for s in seen):
                seen.append(norm)
        self._items = seen[: self._max_items]

    def save(self) -> None:
        """Сохраняет историю в файл. Ошибки записи не критичны."""
        try:
            os.makedirs(
                os.path.dirname(os.path.abspath(self._storage_path)),
                exist_ok=True,
            )
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump({"folders": self._items}, f,
                          ensure_ascii=False, indent=2)
        except OSError:
            # Не удалось сохранить историю — не мешаем работе приложения
            pass

    # ------------------------------------------------------------------
    # Вспомогательное
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize(path: str) -> str:
        """Абсолютный нормализованный путь (без изменения регистра)."""
        if not path or not path.strip():
            return ""
        return os.path.abspath(path.strip())

    @staticmethod
    def _same(a: str, b: str) -> bool:
        """Сравнение путей с учётом регистронезависимости ОС."""
        return os.path.normcase(a) == os.path.normcase(b)