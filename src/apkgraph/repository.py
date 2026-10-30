"""Собственный парсер APKINDEX; сторонние резолверы не используются."""
import io
import json
import re
import tarfile
from urllib.request import urlopen

TIMEOUT = 30
MAX_DOWNLOAD = 64 * 1024 * 1024


def dependency_name(value):
    """Отделить имя зависимости от ограничения версии."""
    return re.split(r"[<>=~]", value, maxsplit=1)[0]


class Repository:
    """Индекс пакетов и виртуальных provides из одного репозитория."""

    def __init__(self, records):
        """Создать таблицы конкретных имен и провайдеров."""
        self.records = records
        self.providers = {}
        for name, record in sorted(records.items()):
            for value in record.get("p", "").split():
                key = dependency_name(value)
                self.providers.setdefault(key, []).append(name)

    def resolve(self, value):
        """Найти единственного провайдера, не скрывая неоднозначность."""
        name = dependency_name(value)
        if name in self.records:
            return name
        choices = self.providers.get(name, [])
        if len(choices) != 1:
            raise ValueError(f"Зависимость {value}: провайдеры {choices}")
        return choices[0]

    def dependencies(self, name):
        """Вернуть зависимости; !conflict не создает ребро графа."""
        if name not in self.records:
            raise ValueError(f"Пакет не найден: {name}")
        values = self.records[name].get("D", "").split()
        return list(dict.fromkeys(self.resolve(x) for x in values
                                  if not x.startswith("!")))


def parse_index(text):
    """Разобрать записи APKINDEX с полями P, V, D и p."""
    records = {}
    for block in text.strip().split("\n\n"):
        fields = dict(line.split(":", 1) for line in block.splitlines()
                      if ":" in line)
        if "P" not in fields:
            continue
        name = fields["P"]
        if name in records:
            raise ValueError(f"Несколько версий {name}: нужен один срез")
        records[name] = fields
    if not records:
        raise ValueError("APKINDEX не содержит пакетов")
    return Repository(records)


def load_remote(url):
    """Скачать и прочитать APKINDEX.tar.gz без распаковки на диск."""
    if not url.endswith("APKINDEX.tar.gz"):
        url = url.rstrip("/") + "/APKINDEX.tar.gz"
    with urlopen(url, timeout=TIMEOUT) as response:
        content = response.read(MAX_DOWNLOAD + 1)
    if len(content) > MAX_DOWNLOAD:
        raise ValueError("Превышен предел размера индекса")
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
        member = archive.getmember("APKINDEX")
        if member.size > MAX_DOWNLOAD:
            raise ValueError("Превышен размер распакованного индекса")
        with archive.extractfile(member) as stream:
            return parse_index(stream.read().decode("utf-8"))


def load_test(path):
    """Загрузить JSON: объект с именами A..Z и списками зависимостей."""
    with open(path, encoding="utf-8") as stream:
        graph = json.load(stream)
    if not isinstance(graph, dict) or not graph:
        raise ValueError("Тестовый граф должен быть непустым объектом")
    for name, deps in graph.items():
        if not re.fullmatch(r"[A-Z]+", name):
            raise ValueError("Имена тестовых пакетов: A..Z")
        if not isinstance(deps, list) or any(
                not isinstance(x, str) or x not in graph for x in deps):
            raise ValueError(f"Неверные зависимости {name}")
    return Repository({n: {"D": " ".join(d)} for n, d in graph.items()})
