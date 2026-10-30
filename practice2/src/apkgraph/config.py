"""Чтение и проверка CSV-конфигурации."""
import csv
import re
from pathlib import Path
from urllib.parse import urlparse

KEYS = {"package", "repository", "test_mode", "output", "max_depth",
        "filter"}
MAX_DEPTH = 200


def load_config(filename):
    """Загрузить CSV key,value; относительные пути считать от CSV."""
    path = Path(filename).resolve()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    if not rows or rows.pop(0) != ["key", "value"]:
        raise ValueError("CSV должен начинаться строкой key,value")
    data = {}
    for row in rows:
        if len(row) != 2 or row[0] in data or row[0] not in KEYS:
            raise ValueError(f"Неверная или повторная строка CSV: {row}")
        data[row[0]] = row[1].strip()
    if data.keys() != KEYS:
        raise ValueError("Необходимо задать все шесть параметров")
    return validate(data, path.parent)


def validate(data, base):
    """Проверить все поля и нормализовать пути."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9+_.-]*", data["package"]):
        raise ValueError("package: недопустимое имя пакета")
    if data["test_mode"] not in {"true", "false"}:
        raise ValueError("test_mode: ожидается true или false")
    data["test_mode"] = data["test_mode"] == "true"
    try:
        data["max_depth"] = int(data["max_depth"])
    except ValueError as error:
        raise ValueError("max_depth: ожидается целое число") from error
    if not 0 <= data["max_depth"] <= MAX_DEPTH:
        raise ValueError(f"max_depth: допустимо 0..{MAX_DEPTH}")
    validate_paths(data, base)
    if data["filter"] and data["filter"] in data["package"]:
        raise ValueError("filter: фильтр исключает корневой пакет")
    return data


def validate_paths(data, base):
    """Проверить репозиторий и имя выходного SVG."""
    if data["test_mode"]:
        source = (base / data["repository"]).resolve()
        if not data["repository"] or not source.is_file():
            raise ValueError("repository: тестовый файл не найден")
        data["repository"] = str(source)
    else:
        url = urlparse(data["repository"])
        if url.scheme not in {"https", "http"} or not url.netloc:
            raise ValueError("repository: ожидается HTTP(S) URL")
    target = Path(data["output"])
    if target.suffix.lower() != ".svg" or target.name == ".svg":
        raise ValueError("output: необходимо имя файла с расширением .svg")
    target = (base / target).resolve()
    if target.exists() and target.is_dir():
        raise ValueError("output: указан каталог")
    data["output"] = str(target)
