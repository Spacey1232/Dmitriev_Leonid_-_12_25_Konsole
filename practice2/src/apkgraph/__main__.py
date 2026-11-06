"""Запуск этапов практической работы."""
import argparse
import json
import tarfile
from urllib.error import URLError
from .config import load_config
from .repository import load_remote, load_test
from .graph import build_graph, load_order
from .render import save


STAGE_CONFIG = 1
STAGE_DIRECT = 2
STAGE_GRAPH = 3
STAGE_ORDER = 4
STAGE_RENDER = 5
STAGES = (STAGE_CONFIG, STAGE_DIRECT, STAGE_GRAPH, STAGE_ORDER,
          STAGE_RENDER)
ERROR_EXIT_CODE = 2


def execute(config, stage):
    """Выполнить выбранный этап с настройками из CSV."""
    if stage == STAGE_CONFIG:
        for key, value in config.items():
            print(f"{key}={value}")
        return
    repo = (load_test if config["test_mode"] else load_remote)(
        config["repository"])
    root = config["package"]
    if stage == STAGE_DIRECT:
        print("\n".join(repo.dependencies(root)) or "Нет зависимостей")
        return
    graph = build_graph(repo, root, config["max_depth"], config["filter"])
    if stage == STAGE_GRAPH:
        print(json.dumps(graph, ensure_ascii=False, indent=2))
    elif stage == STAGE_ORDER:
        print(" -> ".join(load_order(graph)))
    else:
        save(graph, config["output"])
        print(f"Сохранено: {config['output']}")


def main():
    """Разобрать CLI; диагностические ошибки завершать с кодом 2."""
    parser = argparse.ArgumentParser(description="APK graph, вариант 7")
    parser.add_argument("config", help="CSV key,value")
    parser.add_argument("--stage", type=int, choices=STAGES,
                        default=STAGE_RENDER)
    args = parser.parse_args()
    try:
        execute(load_config(args.config), args.stage)
    except (ValueError, OSError, URLError, KeyError,
            tarfile.TarError, RecursionError) as error:
        parser.exit(ERROR_EXIT_CODE, f"Ошибка: {error}\n")


if __name__ == "__main__":
    main()
