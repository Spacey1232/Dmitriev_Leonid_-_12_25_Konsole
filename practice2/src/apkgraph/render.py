"""Mermaid и самостоятельный SVG-рендер одного и того же графа."""
from html import escape
from pathlib import Path

BOX_WIDTH = 220
ROW_HEIGHT = 72


def mermaid(graph):
    """Сформировать Mermaid с безопасными числовыми идентификаторами."""
    ids = {name: f"n{i}" for i, name in enumerate(graph)}
    lines = ["flowchart TD"]
    for name, ident in ids.items():
        lines.append(f'  {ident}["{escape(name, quote=True)}"]')
    for name, deps in graph.items():
        lines.extend(f"  {ids[name]} --> {ids[d]}" for d in deps)
    return "\n".join(lines) + "\n"


def svg(graph):
    """Нарисовать узлы слева и ребра справа; поддержать петли и циклы."""
    height = len(graph) * ROW_HEIGHT + 40
    width = 900
    positions = {n: 40 + i * ROW_HEIGHT for i, n in enumerate(graph)}
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<defs><marker id="arrow" markerWidth="10" '
             'markerHeight="10" refX="9" refY="3" orient="auto">'
             '<path d="M0,0 L0,6 L9,3 z" fill="#52677e"/>'
             '</marker></defs>']
    for i, (name, deps) in enumerate(graph.items()):
        for j, child in enumerate(deps):
            y1, y2 = positions[name], positions[child]
            bend = 320 + ((i + j) % 10) * 45
            lines.append(f'<path d="M260,{y1} C{bend},{y1 - 25} '
                         f'{bend},{y2 + 25} 260,{y2 + 8}" fill="none" '
                         'stroke="#52677e" marker-end="url(#arrow)"/>')
    for name, y in positions.items():
        lines.append(f'<rect x="40" y="{y - 20}" width="{BOX_WIDTH}" '
                     'height="40" rx="8" fill="#edf4ff" '
                     'stroke="#3668b1"/>')
        lines.append(f'<text x="50" y="{y + 5}" font-size="14" '
                     f'font-family="monospace">{escape(name)}</text>')
    return "\n".join(lines + ["</svg>"])


def save(graph, output):
    """Сохранить SVG и соседний файл .mmd."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg(graph), encoding="utf-8")
    path.with_suffix(".mmd").write_text(mermaid(graph), encoding="utf-8")
