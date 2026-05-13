from collections import deque


# =========================================================
# PART (a)
# Conflict graph for guard coloring
# =========================================================

def build_conflict_graph(selected_guards, coverage_matrix):

    graph = {
        g: set()
        for g in selected_guards
    }

    n_rectangles = len(coverage_matrix[0])

    for r in range(n_rectangles):

        guards_covering = [
            g
            for g in selected_guards
            if coverage_matrix[g][r] == 1
        ]

        for i in range(len(guards_covering)):
            for j in range(i + 1, len(guards_covering)):

                g1 = guards_covering[i]
                g2 = guards_covering[j]

                graph[g1].add(g2)
                graph[g2].add(g1)

    return graph

def exact_coloring(graph):

    nodes = list(graph.keys())

    # order nodes by degree (important for pruning)
    nodes.sort(key=lambda x: len(graph[x]), reverse=True)

    n = len(nodes)

    best_coloring = {}
    best_k = float("inf")

    coloring = {}

    def backtrack(i, used_colors):

        nonlocal best_coloring, best_k

        # pruning
        if used_colors >= best_k:
            return

        if i == n:
            best_coloring = coloring.copy()
            best_k = used_colors
            return

        node = nodes[i]

        forbidden = {
            coloring[nbr]
            for nbr in graph[node]
            if nbr in coloring
        }

        for c in range(used_colors):

            if c not in forbidden:
                coloring[node] = c
                backtrack(i + 1, used_colors)
                del coloring[node]

        # try new color
        coloring[node] = used_colors
        backtrack(i + 1, used_colors + 1)
        del coloring[node]

    backtrack(0, 0)

    return best_coloring, best_k


# =========================================================
# PART (b)
# Rectangle adjacency graph
# =========================================================

def build_rectangle_graph(instance):

    n = len(instance.rectangles)

    graph = {
        i: set()
        for i in range(n)
    }

    for i in range(n):

        ri = set(instance.rectangles[i].vertices)

        for j in range(i + 1, n):

            rj = set(instance.rectangles[j].vertices)

            # adjacent if share at least one vertex
            if ri & rj:

                graph[i].add(j)
                graph[j].add(i)

    return graph


def bfs_expand(rect_graph, start_rectangles, D):

    visited = set(start_rectangles)

    queue = deque()

    for r in start_rectangles:
        queue.append((r, 0))

    while queue:

        node, dist = queue.popleft()

        if dist == D:
            continue

        for neigh in rect_graph[node]:

            if neigh not in visited:

                visited.add(neigh)

                queue.append((neigh, dist + 1))

    return visited


# =========================================================
# Expanded coverage sets for distance D
# =========================================================

def build_expanded_coverage_sets(instance, D):

    rect_graph = build_rectangle_graph(instance)

    vertex_index = {
        v: i
        for i, v in enumerate(instance.vertices)
    }

    coverage_sets = [
        set()
        for _ in instance.vertices
    ]

    # direct coverage
    for rect_idx, rect in enumerate(instance.rectangles):

        for v in rect.vertices:

            vi = vertex_index[v]

            coverage_sets[vi].add(rect_idx)

    # expand with BFS
    expanded = []

    for cov in coverage_sets:

        expanded_cov = bfs_expand(
            rect_graph,
            list(cov),
            D
        )

        expanded.append(sorted(list(expanded_cov)))

    return expanded