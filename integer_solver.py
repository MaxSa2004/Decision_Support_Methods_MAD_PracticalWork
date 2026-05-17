from ortools.sat.python import cp_model

class IntegerSolver:
    def __init__(self, coverage_matrix, required=None):
        self.A = coverage_matrix
        self.m = len(coverage_matrix)
        self.n = len(coverage_matrix[0])
        # required: indices of rectangles that must be covered (None = all)
        self.required = list(required) if required is not None else list(range(self.n))

    def solve(self):
        model = cp_model.CpModel()
        x = [model.NewBoolVar(f'x{i}') for i in range(self.m)]

        for j in self.required:
            model.Add(sum(x[i] for i in range(self.m) if self.A[i][j] == 1) >= 1)

        model.Minimize(sum(x))

        solver = cp_model.CpSolver()
        solver.Solve(model)

        return [i for i in range(self.m) if solver.Value(x[i]) == 1]