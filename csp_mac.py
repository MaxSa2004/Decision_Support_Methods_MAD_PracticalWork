from collections import deque

class MACSolver:
    def __init__(self, coverage_matrix, required=None):
        self.A = coverage_matrix
        self.m = len(coverage_matrix)
        self.n = len(coverage_matrix[0]) if self.m > 0 else 0
        # required: 0-based indices of rectangles that must be covered (None = all)
        self.required = list(required) if required is not None else list(range(self.n))

        # Scope of each rectangle constraint: vertices that can cover that rectangle.
        self.rect_to_vars = {
            r: [i for i in range(self.m) if self.A[i][r] == 1]
            for r in self.required
        }

        # For fast queue updates after domain reductions.
        self.var_to_rects = {i: [] for i in range(self.m)}
        for r, vars_covering_r in self.rect_to_vars.items():
            for i in vars_covering_r:
                self.var_to_rects[i].append(r)

    def _initial_domains(self):
        return [set([0, 1]) for _ in range(self.m)]

    def _has_support(self, var, value, rect, domains):
        # Constraint per rectangle: at least one covering variable must be 1.
        covers = self.A[var][rect] == 1
        if covers and value == 1:
            return True

        for other in self.rect_to_vars[rect]:
            if other == var:
                continue
            if 1 in domains[other]:
                return True
        return False

    def _revise(self, var, rect, domains):
        revised = False
        current = list(domains[var])

        for value in current:
            if not self._has_support(var, value, rect, domains):
                domains[var].remove(value)
                revised = True

        return revised

    def _ac3(self, domains, queue=None):
        if queue is None:
            queue = deque()
            for r, scope in self.rect_to_vars.items():
                for var in scope:
                    queue.append((var, r))
        else:
            queue = deque(queue)

        while queue:
            var, rect = queue.popleft()

            if self._revise(var, rect, domains):
                if not domains[var]:
                    return False

                # If var changed, neighboring vars in the same constraints may lose support.
                for other_rect in self.var_to_rects[var]:
                    for other_var in self.rect_to_vars[other_rect]:
                        if other_var != var:
                            queue.append((other_var, other_rect))

        return True

    def _is_complete(self, domains):
        return all(len(dom) == 1 for dom in domains)

    def _extract_assignment(self, domains):
        return [next(iter(dom)) for dom in domains]

    def _select_unassigned_var(self, domains):
        candidates = [i for i in range(self.m) if len(domains[i]) > 1]
        if not candidates:
            return None
        # MRV: choose variable with smallest domain (>1).
        return min(candidates, key=lambda i: len(domains[i]))

    def _backtrack_mac(self, domains):
        if self._is_complete(domains):
            assignment = self._extract_assignment(domains)
            if all(any(assignment[i] == 1 for i in self.rect_to_vars[r]) for r in self.required):
                return assignment
            return None

        var = self._select_unassigned_var(domains)
        if var is None:
            return None

        for value in [0, 1]:
            if value not in domains[var]:
                continue

            new_domains = [set(dom) for dom in domains]
            new_domains[var] = set([value])

            local_queue = []
            for rect in self.var_to_rects[var]:
                for scope_var in self.rect_to_vars[rect]:
                    local_queue.append((scope_var, rect))

            if self._ac3(new_domains, local_queue):
                result = self._backtrack_mac(new_domains)
                if result is not None:
                    return result

        return None

    def solve(self):
        # Early unsat: a required rectangle has no covering vertices.
        if any(len(self.rect_to_vars[r]) == 0 for r in self.required):
            return None

        domains = self._initial_domains()
        if not self._ac3(domains):
            return None

        return self._backtrack_mac(domains)