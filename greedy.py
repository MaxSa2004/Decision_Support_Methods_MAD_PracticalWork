class GreedySolver:
    def __init__(self, coverage_matrix, required=None):
        self.A = coverage_matrix
        self.num_vertices = len(coverage_matrix)
        self.num_rectangles = len(coverage_matrix[0])
        # required: indices of rectangles that must be covered (None = all)
        self.required = set(required) if required is not None else set(range(self.num_rectangles))

    def solve(self):
        uncovered = set(self.required)
        guards = []

        while uncovered:
            best_vertex = None
            best_cover = set()

            for v in range(self.num_vertices):
                current_cover = {r for r in uncovered if self.A[v][r] == 1 and r in self.required}
                if len(current_cover) > len(best_cover):
                    best_cover = current_cover
                    best_vertex = v

            guards.append(best_vertex)
            uncovered -= best_cover

        return guards