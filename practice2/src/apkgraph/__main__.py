"""Запуск этапов практической работы."""
import argparse
import json
import tarfile
from urllib.error import URLError
from .config import load_config
from .repository import load_remote, load_test
from .graph import build_graph, load_order
from .render import save


def execute(config, stage):
    """Выполнить выбранный этап с настройками из CSV."""
    if stage == 1:
        for key, value in config.items():
            print(f"{key}={value}")
        return
    repo = (load_test if config["test_mode"] else load_remote)(
        config["repository"])
    root = config["package"]
    if stage == 2:
        print("\n".join(repo.dependencies(root)) or "Нет зависимостей")
        return
    graph = build_graph(repo, root, config["max_depth"], config["filter"])
    if stage == 3:
        print(json.dumps(graph, ensure_ascii=False, indent=2))
    elif stage == 4:
        print(" -> ".join(load_order(graph)))
    else:
        save(graph, config["output"])
        print(f"Сохранено: {config['output']}")


def main():
    """Разобрать CLI; диагностические ошибки завершать с кодом 2."""
    parser = argparse.ArgumentParser(description="APK graph, вариант 7")
    parser.add_argument("config", help="CSV key,value")
    parser.add_argument("--stage", type=int, choices=range(1, 6), default=5)
    args = parser.parse_args()
    try:
        execute(load_config(args.config), args.stage)
    except (ValueError, OSError, URLError, KeyError,
            tarfile.TarError, RecursionError) as error:
        parser.exit(2, f"Ошибка: {error}\n")


if __name__ == "__main__":
    main()
