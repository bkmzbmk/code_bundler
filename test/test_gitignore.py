"""Проверка правил .gitignore без реальной файловой системы."""
from model.gitignore_rules import GitignoreRules


def check(gi: GitignoreRules, path: str, is_dir: bool, expected: bool):
    result = gi.is_ignored(path, is_dir)
    status = "OK " if result == expected else "FAIL"
    print(f"  [{status}] {path!r} (dir={is_dir}) "
          f"-> {result} (ожидалось {expected})")


def main():
    gi = GitignoreRules()
    gi.load_lines([
        "# комментарий",
        "build/",            # папка build где угодно
        "*.log",            # любые .log
        "/secret.txt",      # только в корне
        "temp",             # temp где угодно
        "!important.log",   # но important.log не игнорим
        "docs/*.tmp",       # .tmp внутри docs (якорь из-за /)
    ])

    print("Тесты .gitignore:")
    check(gi, "build", True, True)
    check(gi, "src/build", True, True)
    check(gi, "src/build/main.o", False, True)   # содержимое build/
    check(gi, "app.log", False, True)
    check(gi, "logs/app.log", False, True)
    check(gi, "important.log", False, False)     # отрицание !
    check(gi, "secret.txt", False, True)
    check(gi, "sub/secret.txt", False, False)    # якорь /: только корень
    check(gi, "temp", True, True)
    check(gi, "a/temp/b.txt", False, True)
    check(gi, "docs/note.tmp", False, True)
    check(gi, "other/note.tmp", False, False)    # docs/ — якорь
    check(gi, "main.cpp", False, False)          # не игнорим


if __name__ == "__main__":
    main()