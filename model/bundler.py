"""Сборка списка файлов в единый текст с метками START/END."""
from __future__ import annotations

import os
import re

from config import FILE_START_TEMPLATE, FILE_END_TEMPLATE
from model.file_reader import read_text


class Bundler:
    """Собирает файлы в один текстовый блок с метками.

    Опционально удаляет комментарии и/или пустые строки для
    экономии токенов."""

    def __init__(
        self,
        strip_comments: bool = False,
        strip_blank_lines: bool = False,
    ) -> None:
        self.strip_comments = strip_comments
        self.strip_blank_lines = strip_blank_lines

    def bundle(self, file_paths: list[str], root_path: str) -> str:
        """Собирает файлы в текст.

        Args:
            file_paths: абсолютные пути к файлам.
            root_path:  корень проекта (для вычисления rel_path в метках).
        """
        root_path = os.path.abspath(root_path)
        blocks: list[str] = []

        for path in file_paths:
            abs_path = os.path.abspath(path)
            rel_path = os.path.relpath(abs_path, root_path).replace("\\", "/")

            content = self._read_and_process(abs_path)

            start = FILE_START_TEMPLATE.format(path=rel_path)
            end = FILE_END_TEMPLATE.format(path=rel_path)
            blocks.append(f"{start}\n{content}\n{end}")

        return "\n\n".join(blocks)

    def _read_and_process(self, path: str) -> str:
        """Читает файл и применяет опции обработки."""
        text = read_text(path)
        ext = os.path.splitext(path)[1].lower()

        if self.strip_comments:
            text = self._remove_comments(text, ext)
        if self.strip_blank_lines:
            text = self._remove_blank_lines(text)

        return text.rstrip("\n")

    # ------------------------------------------------------------------
    # Обработка (простые эвристики; не полноценный парсер)
    # ------------------------------------------------------------------
    def _remove_comments(self, text: str, ext: str) -> str:
        """Удаляет комментарии. Простые regex-эвристики.

        ВНИМАНИЕ: не учитывает комментарии внутри строковых литералов.
        Для отправки ИИ это приемлемо."""
        if ext in {".py", ".pyw"}:
            # Python: # ... до конца строки
            text = re.sub(r"#.*", "", text)
        else:
            # C/C++: /* ... */ и // ...
            text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
            text = re.sub(r"//.*", "", text)
        return text

    def _remove_blank_lines(self, text: str) -> str:
        """Схлопывает подряд идущие пустые строки в одну."""
        lines = [ln.rstrip() for ln in text.splitlines()]
        result: list[str] = []
        prev_blank = False
        for ln in lines:
            is_blank = (ln == "")
            if is_blank and prev_blank:
                continue
            result.append(ln)
            prev_blank = is_blank
        return "\n".join(result)