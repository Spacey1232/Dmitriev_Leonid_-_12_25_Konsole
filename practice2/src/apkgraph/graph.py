"""Рекурсивный BFS по уровням и операции над графом."""


def build_graph(repo, root, max_depth, exclude=""):
    """Построить BFS; корень имеет глубину 0, граница не раскрывается."""
    graph = {root: []}
    visited = {root}
    if root not in repo.records:
        raise ValueError(f"Пакет не найден: {root}")

    def level(frontier, depth):
        """Рекурсивно обработать целиком очередной уровень BFS."""
        if not frontier or depth >= max_depth:
            return
        following = []
        for name in frontier:
            for child in repo.dependencies(name):
                if exclude and exclude in child:
                    continue
                graph[name].append(child)
                if child not in visited:
                    visited.add(child)
                    graph[child] = []
                    following.append(child)
        level(following, depth + 1)

    level([root], 0)
    return graph


def load_order(graph):
    """Топологический порядок: зависимости раньше потребителей."""
    remaining = {name: len(set(deps)) for name, deps in graph.items()}
    users = {name: [] for name in graph}
    for name, deps in graph.items():
        for child in set(deps):
            users[child].append(name)
    ready = sorted(n for n, count in remaining.items() if not count)
    result = []
    while ready:
        name = ready.pop(0)
        result.append(name)
        for user in sorted(users[name]):
            remaining[user] -= 1
            if not remaining[user]:
                ready.append(user)
    if len(result) != len(graph):
        raise ValueError("Цикл: линейного порядка загрузки не существует")
    return result
