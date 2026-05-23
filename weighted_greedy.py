import heapq


class WeightedGreedySolver:
    '''
    Versao greedy diferente: em vez de maximizar apenas quantidade de cobertura,
    prioriza retangulos com menos opcoes de guarda (peso inverso do grau).
    '''

    def __init__(self, coverage_matrix, required=None):
        self.A = coverage_matrix
        self.num_vertices = len(coverage_matrix)
        self.num_rectangles = len(coverage_matrix[0]) if self.num_vertices > 0 else 0

        # required: indices dos retangulos que tem de ser cobertos (None = todos)
        self.required = set(required) if required is not None else set(range(self.num_rectangles))

    def solve(self):
        if not self.required:
            return []

        # rect_to_vertices[r] = lista de vertices que cobrem r
        rect_to_vertices = {r: [] for r in self.required}
        vertex_to_required = [[] for _ in range(self.num_vertices)]
        for v in range(self.num_vertices):
            row = self.A[v]
            for r in self.required:
                if row[r] == 1:
                    rect_to_vertices[r].append(v)
                    vertex_to_required[v].append(r)

        # Se existir um retangulo requerido sem cobertura possivel, nao ha solucao viavel.
        for r in self.required:
            if not rect_to_vertices[r]:
                return None

        # Peso de cada retangulo: mais raro => maior peso.
        weights = {r: 1.0 / len(rect_to_vertices[r]) for r in self.required}

        # gain[v] = soma dos pesos dos retangulos ainda nao cobertos que v cobre.
        gain = [0.0] * self.num_vertices
        for r in self.required:
            w = weights[r]
            for v in rect_to_vertices[r]:
                gain[v] += w

        # Max-heap por ganho (heapq e min-heap, por isso usamos negativo).
        heap = [(-gain[v], v) for v in range(self.num_vertices)]
        heapq.heapify(heap)

        uncovered = set(self.required)
        guards = []

        while uncovered:
            best_vertex = None

            # Lazy validation para evitar rebuild completo do heap.
            while heap:
                neg_val, v = heapq.heappop(heap)
                if -neg_val == gain[v]:
                    best_vertex = v
                    break

            if best_vertex is None:
                return None

            covered_now = [r for r in vertex_to_required[best_vertex] if r in uncovered]
            if not covered_now:
                return None

            guards.append(best_vertex)

            # Cada aresta (v, r) e atualizada no maximo uma vez, quando r e coberto.
            for r in covered_now:
                uncovered.remove(r)
                w = weights[r]
                for u in rect_to_vertices[r]:
                    gain[u] -= w
                    heapq.heappush(heap, (-gain[u], u))

        return guards