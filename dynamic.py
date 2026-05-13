class DPSolver:
    def __init__(self, coverage_sets, n_rectangles):
        self.coverage_sets = coverage_sets
        self.n = n_rectangles

    def solve(self):
        from collections import deque

        full = (1 << self.n) - 1
        dp = {0: []}
        queue = deque([0])

        while queue:
            state = queue.popleft()
            guards = dp[state]

            if state == full:
                return guards

            for v, cov in enumerate(self.coverage_sets):
                new_state = state
                for r in cov:
                    new_state |= (1 << r)

                if new_state not in dp or len(dp[new_state]) > len(guards)+1:
                    dp[new_state] = guards + [v]
                    queue.append(new_state)