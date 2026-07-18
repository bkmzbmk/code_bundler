"""Ручной тест Этапа 1. Запуск: python test_stage1.py <путь_к_проекту>"""
import sys
from model.app_model import AppModel


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python test_stage1.py <путь_к_проекту>")
        return

    root = sys.argv[1]
    model = AppModel()

    print(f"Сканирую: {root}")
    tree = model.load_project(root)

    files = [n.rel_path for n in tree.iter_files()]
    print(f"Найдено файлов кода: {len(files)}")
    for f in files[:20]:
        print("  ", f)
    if len(files) > 20:
        print(f"  ... ещё {len(files) - 20}")

    if not files:
        print("Файлы не найдены — нечего собирать.")
        return

    # Собираем первые 3 файла для проверки
    sample = files[:3]
    print(f"\nСобираю {len(sample)} файла(ов)...")
    bundle = model.build_bundle(sample, strip_comments=False,
                                strip_blank=False)

    tokens = model.count_tokens(bundle)
    mode = "tiktoken" if model.tokens_available() else "оценка"
    print(f"Токенов: {tokens} ({mode})")
    print("-" * 60)
    print(bundle[:1500])
    print("-" * 60)
    if len(bundle) > 1500:
        print("(вывод обрезан)")


if __name__ == "__main__":
    main()