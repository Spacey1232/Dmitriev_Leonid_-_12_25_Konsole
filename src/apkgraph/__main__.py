"""Точка входа CLI."""
import argparse
from .config import load_config


def main():
    """Вывести проверенные настройки."""
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    args = parser.parse_args()
    try:
        for key, value in load_config(args.config).items():
            print(f"{key}={value}")
    except (ValueError, OSError) as error:
        parser.exit(2, f"Ошибка: {error}\n")


if __name__ == "__main__":
    main()
