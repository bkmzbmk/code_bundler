"""Тест анализатора зависимостей.
Запуск: python test_stage2.py <путь_к_проекту> <rel/path/to/file> [depth]
Пример: python test_stage2.py ./myproj src/main.cpp 2
"""
import sys
from model.app_model import AppModel


def main() -> None:
    if len(sys.argv) < 3:
        print("Использование: python test_stage2.py "
              "<путь_к_проекту> <rel/path/file> [depth]")
        return

    root = sys.argv[1]
    start_rel = sys.argv[2].replace("\\", "/")
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    model = AppModel()
    tree = model.load_project(root)

    node = tree.find_by_rel_path(start_rel)
    if node is None:
        print(f"Файл не найден в дереве: {start_rel}")
        print("Доступные файлы (первые 30):")
        for n in list(tree.iter_files())[:30]:
            print("  ", n.rel_path)
        return

    print(f"Стартовый файл: {start_rel}")
    print(f"Глубина: {depth}")
    print("-" * 60)

    resolved = model.resolve_dependencies([start_rel], depth)
    print(f"Всего файлов после разрешения: {len(resolved)}")
    for r in resolved:
        mark = " <- START" if r == start_rel else ""
        print(f"  {r}{mark}")

    print("-" * 60)
    print("Прямые зависимости стартового файла:")
    edges = model.get_dependency_edges()
    for dep in sorted(edges.get(start_rel, [])):
        print(f"  {start_rel} -> {dep}")

    print("-" * 60)
    bundle = model.build_bundle(resolved)
    tokens = model.count_tokens(bundle)
    mode = "tiktoken" if model.tokens_available() else "оценка"
    print(f"Итоговый bundle: {len(bundle)} символов, "
          f"{tokens} токенов ({mode})")


if __name__ == "__main__":
    main()