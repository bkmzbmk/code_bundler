"""Разбор и применение правил .gitignore.

Поддерживается основное подмножество синтаксиса gitignore:
  - комментарии (#) и пустые строки;
  - отрицание (!pattern) — возвращает файл обратно;
  - якорь в начале (/pattern) — только от корня;
  - каталог (pattern/) — совпадает только с папками;
  - glob-символы: *, ?, ** (через fnmatch по сегментам).

Пути для проверки задаём ОТНОСИТЕЛЬНО корня проекта, с "/" как
разделителем."""
from __future__ import annotations

import fnmatch
import os


class _Rule:
    """Одно скомпилированное правило .gitignore."""

    def __init__(self, pattern: str) -> None:
        self.negation = False        # правило начинается с "!"
        self.dir_only = False        # правило заканчивается на "/"
        self.anchored = False        # правило привязано к корню ("/" внутри/начале)
        self.pattern = ""            # очищенный шаблон (без !, /)
        self._parse(pattern)

    def _parse(self, raw: str) -> None:
        p = raw

        if p.startswith("!"):
            self.negation = True
            p = p[1:]

        # экранированные ведущие символы (\#, \!) — снимаем слэш
        if p.startswith("\\#") or p.startswith("\\!"):
            p = p[1:]

        if p.endswith("/"):
            self.dir_only = True
            p = p[:-1]

        # Якорь: слэш в начале ИЛИ внутри (не считая хвостового)
        if p.startswith("/"):
            self.anchored = True
            p = p[1:]
        elif "/" in p:
            # слэш где-то в середине -> путь считается от корня
            self.anchored = True

        self.pattern = p

    def matches(self, rel_path: str, is_dir: bool) -> bool:
        """rel_path — относительный путь с "/" (например 'src/build')."""
        if not self.pattern:
            return False
        if self.dir_only and not is_dir:
            return False

        if self.anchored:
            return self._match_anchored(rel_path)
        return self._match_floating(rel_path)

    def _match_anchored(self, rel_path: str) -> bool:
        """Совпадение от корня. Также совпадает содержимое папки."""
        if self._fnmatch_path(rel_path, self.pattern):
            return True
        # Если правило указывает на папку — игнорируем и её содержимое
        prefix = self.pattern.rstrip("/") + "/"
        return (rel_path + "/").startswith(prefix)

    def _match_floating(self, rel_path: str) -> bool:
        """Совпадение по любому хвосту пути (правило без якоря).

        Проверяем и полный путь, и каждый его подхвост, начинающийся
        с сегмента."""
        segments = rel_path.split("/")
        for i in range(len(segments)):
            tail = "/".join(segments[i:])
            if self._fnmatch_path(tail, self.pattern):
                return True
        return False

    @staticmethod
    def _fnmatch_path(path: str, pattern: str) -> bool:
        """fnmatch с учётом '**'. Для простоты '**' -> обычный '*'
        внутри fnmatch (fnmatch и так пропускает '/' через '*')."""
        # fnmatch не различает '/', поэтому '*' матчит и разделители.
        # Для наших задач (игнор папок/файлов) этого достаточно.
        pat = pattern.replace("**", "*")
        return fnmatch.fnmatch(path, pat)


class GitignoreRules:
    """Набор правил из одного или нескольких .gitignore-файлов."""

    def __init__(self) -> None:
        self._rules: list[_Rule] = []

    @classmethod
    def from_file(cls, gitignore_path: str) -> "GitignoreRules":
        obj = cls()
        obj.load_file(gitignore_path)
        return obj

    def load_file(self, gitignore_path: str) -> None:
        """Загружает правила из файла (если он существует)."""
        if not os.path.isfile(gitignore_path):
            return
        try:
            with open(gitignore_path, "r", encoding="utf-8",
                      errors="replace") as f:
                lines = f.readlines()
        except OSError:
            return
        self.load_lines(lines)

    def load_lines(self, lines: list[str]) -> None:
        for raw in lines:
            line = raw.rstrip("\n").rstrip("\r")
            # убираем хвостовые пробелы (кроме экранированных "\ ")
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            self._rules.append(_Rule(line))

    def has_rules(self) -> bool:
        return bool(self._rules)

    def is_ignored(self, rel_path: str, is_dir: bool) -> bool:
        """Проверка пути по всем правилам с учётом отрицаний (!).

        Последнее совпавшее правило побеждает (как в git)."""
        rel_path = rel_path.replace("\\", "/").strip("/")
        if not rel_path:
            return False

        ignored = False
        for rule in self._rules:
            if rule.matches(rel_path, is_dir):
                ignored = not rule.negation
        return ignored