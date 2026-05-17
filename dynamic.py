class DPSolver:
    def __init__(self, coverage_sets, n_rectangles, required=None):
        self.coverage_sets = coverage_sets
        self.n = n_rectangles
        # required: indices of rectangles that must be covered (None = all)
        required_indices = required if required is not None else range(n_rectangles)
        self.full = 0
        for r in required_indices:
            self.full |= (1 << r)

    def solve(self):
        from collections import deque

        full = self.full
        dp = {0: []}
        queue = deque([0])

        while queue:
            state = queue.popleft()
            guards = dp[state]

            if state & full == full:
                return guards

            for v, cov in enumerate(self.coverage_sets):
                new_state = state
                for r in cov:
                    new_state |= (1 << r)

                if new_state not in dp or len(dp[new_state]) > len(guards)+1:
                    dp[new_state] = guards + [v]
                    queue.append(new_state)