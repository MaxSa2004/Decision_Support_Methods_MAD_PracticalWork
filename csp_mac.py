class MACSolver:
    def __init__(self, coverage_matrix):
        self.A = coverage_matrix
        self.m = len(coverage_matrix)
        self.n = len(coverage_matrix[0])

    def is_covered(self, assignment, rect):
        return any(assignment[i] == 1 and self.A[i][rect] == 1 for i in range(self.m))

    def valid_partial(self, assignment):
        for r in range(self.n):
            possible = False
            for i in range(self.m):
                if assignment[i] is None and self.A[i][r] == 1:
                    possible = True
                if assignment[i] == 1 and self.A[i][r] == 1:
                    possible = True
            if not possible:
                return False
        return True

    def backtrack(self, assignment, idx=0):
        if idx == self.m:
            if all(self.is_covered(assignment, r) for r in range(self.n)):
                return assignment
            return None

        for val in [0,1]:
            assignment[idx] = val
            if self.valid_partial(assignment):
                result = self.backtrack(assignment, idx+1)
                if result:
                    return result
            assignment[idx] = None
        return None

    def solve(self):
        return self.backtrack([None]*self.m)