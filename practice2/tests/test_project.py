"""Проверки алгоритмов, форматов, ошибок и CLI."""
import csv
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from apkgraph.config import load_config, validate
from apkgraph.repository import Repository, parse_index, load_remote
from apkgraph.graph import build_graph, load_order
from apkgraph.render import mermaid, svg


class GraphTests(unittest.TestCase):
    """Глубина, фильтрация, циклы и порядок."""

    def setUp(self):
        self.repo = Repository({
            "A": {"D": "B C"}, "B": {"D": "D"},
            "C": {"D": "D"}, "D": {"D": ""}})

    def test_bfs(self):
        graph = build_graph(self.repo, "A", 20)
        self.assertEqual(list(graph), ["A", "B", "C", "D"])
        self.assertEqual(graph["C"], ["D"])

    def test_depth_zero(self):
        self.assertEqual(build_graph(self.repo, "A", 0), {"A": []})

    def test_depth_one(self):
        self.assertEqual(build_graph(self.repo, "A", 1),
                         {"A": ["B", "C"], "B": [], "C": []})

    def test_filter(self):
        graph = build_graph(self.repo, "A", 20, "B")
        self.assertNotIn("B", graph)
        self.assertEqual(graph["A"], ["C"])

    def test_cycle(self):
        repo = Repository({"A": {"D": "B"}, "B": {"D": "A"}})
        graph = build_graph(repo, "A", 20)
        self.assertEqual(graph, {"A": ["B"], "B": ["A"]})
        with self.assertRaisesRegex(ValueError, "Цикл"):
            load_order(graph)

    def test_self_loop(self):
        graph = build_graph(Repository({"A": {"D": "A"}}), "A", 10)
        self.assertEqual(graph, {"A": ["A"]})

    def test_order(self):
        graph = build_graph(self.repo, "A", 20)
        order = load_order(graph)
        for name, deps in graph.items():
            for dep in deps:
                self.assertLess(order.index(dep), order.index(name))

    def test_missing(self):
        with self.assertRaises(ValueError):
            build_graph(self.repo, "Z", 20)

    def test_render(self):
        graph = build_graph(self.repo, "A", 20)
        self.assertIn("n0 --> n1", mermaid(graph))
        import xml.etree.ElementTree as xml
        tree = xml.fromstring(svg(graph))
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(len(tree.findall("s:text", ns)), len(graph))


class RepositoryTests(unittest.TestCase):
    """Парсер и извлечение архива без сетевой зависимости тестов."""

    def test_virtual_and_conflicts(self):
        repo = parse_index("P:app\nD:so:libc.so=1 !bad\n\n"
                           "P:musl\np:so:libc.so=1\n")
        self.assertEqual(repo.dependencies("app"), ["musl"])

    def test_ambiguous(self):
        repo = Repository({"a": {"p": "v"}, "b": {"p": "v"}})
        with self.assertRaises(ValueError):
            repo.resolve("v")

    def test_empty(self):
        with self.assertRaises(ValueError):
            parse_index("")

    def test_archive(self):
        payload = b"P:a\nD:b\n\nP:b\n"
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            member = tarfile.TarInfo("APKINDEX")
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
        with patch("apkgraph.repository.urlopen") as request:
            request.return_value.__enter__.return_value.read.return_value = (
                buffer.getvalue())
            self.assertEqual(load_remote("https://example.test").
                             dependencies("a"), ["b"])


class ConfigTests(unittest.TestCase):
    """Ошибки всех шести параметров конфигурации."""

    def valid(self):
        return dict(package="app", repository="https://example.test/repo",
                    test_mode="false", output="graph.svg", max_depth="4",
                    filter="")

    def test_invalid_fields(self):
        cases = [("package", "bad name"), ("repository", "file:///tmp"),
                 ("test_mode", "yes"), ("output", "x.png"),
                 ("max_depth", "-1"), ("max_depth", "x"),
                 ("filter", "app")]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                data = self.valid()
                data[key] = value
                with self.assertRaises(ValueError):
                    validate(data, Path.cwd())

    def test_missing_test_file(self):
        data = self.valid()
        data.update(test_mode="true", repository="/missing/graph.json")
        with self.assertRaises(ValueError):
            validate(data, Path.cwd())

    def test_csv_duplicate(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.csv"
            path.write_text("key,value\npackage,A\npackage,B\n")
            with self.assertRaises(ValueError):
                load_config(path)

    def test_cli_cycle_exit(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "apkgraph",
             str(root / "examples/cycle.csv"), "--stage", "4"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Цикл", result.stderr)
