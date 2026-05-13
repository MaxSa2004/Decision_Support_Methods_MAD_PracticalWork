class Rectangle:
    def __init__(self, rid, vertices):
        self.id = rid
        self.vertices = vertices


class Instance:
    def __init__(self, k):
        self.k = k
        self.rectangles = []

        # ordered unique vertices
        self.vertices = []


def parse_instances(filename):
    with open(filename, 'r') as f:
        raw_lines = [ln.strip() for ln in f if ln.strip()]

    instances = []
    i = 0

    # optional number of instances
    n = None
    if (
        i + 1 < len(raw_lines)
        and len(raw_lines[i].split()) == 1
        and len(raw_lines[i + 1].split()) == 1
    ):
        try:
            n = int(raw_lines[i])
            i += 1
        except ValueError:
            pass

    instances_parsed = 0

    while i < len(raw_lines) and (n is None or instances_parsed < n):

        # instance size k
        if len(raw_lines[i].split()) != 1:
            raise ValueError(
                f"Expected instance grid size k at line {i+1}: '{raw_lines[i]}'"
            )

        k = int(raw_lines[i])
        inst = Instance(k)
        i += 1

        # read rectangles
        while i < len(raw_lines):

            parts = raw_lines[i].split()

            # next instance starts
            if len(parts) == 1:
                break

            try:
                nums = list(map(int, parts))
            except ValueError:
                raise ValueError(
                    f"Non-integer token on line {i+1}: '{raw_lines[i]}'"
                )

            rid = nums[0]
            m = nums[1]
            coords = nums[2:]

            if len(coords) != 2 * m:
                raise ValueError(
                    f"Expected {2*m} coord values for face {rid}, "
                    f"got {len(coords)} on line {i+1}"
                )

            vertices = []

            for j in range(0, len(coords), 2):
                v = (coords[j], coords[j + 1])

                vertices.append(v)

                # keep unique ordered vertices
                if v not in inst.vertices:
                    inst.vertices.append(v)

            inst.rectangles.append(Rectangle(rid, vertices))
            i += 1

        instances.append(inst)
        instances_parsed += 1

    return instances


def build_coverage_sets(instance):

    vertex_index = {
        v: i for i, v in enumerate(instance.vertices)
    }

    coverage_sets = [[] for _ in instance.vertices]

    for rect_idx, rect in enumerate(instance.rectangles):

        for v in rect.vertices:
            vi = vertex_index[v]
            coverage_sets[vi].append(rect_idx)

    return coverage_sets, instance.vertices


if __name__ == '__main__':
    import sys
    import json
    try:
        # try package-relative imports first
        from . import dynamic as dynamic_mod
        from . import greedy as greedy_mod
        from . import integer_solver as integer_mod
        from . import csp_mac as csp_mod
        try:
            from . import extensions as extensions_mod
        except Exception:
            extensions_mod = None
    except Exception:
        # fallback to importing modules from the same folder when running as script
        import importlib, os, sys
        pkg_dir = os.path.dirname(__file__)
        if pkg_dir not in sys.path:
            sys.path.insert(0, pkg_dir)

        dynamic_mod = importlib.import_module('dynamic')
        greedy_mod = importlib.import_module('greedy')
        integer_mod = importlib.import_module('integer_solver')
        csp_mod = importlib.import_module('csp_mac')
        # optional extensions module
        try:
            extensions_mod = importlib.import_module('extensions')
        except Exception:
            extensions_mod = None

    fname = sys.argv[1] if len(sys.argv) > 1 else 'res'

    # method can be passed as second arg: e.g. `python parse.py res dynamic`
    method_arg = sys.argv[2] if len(sys.argv) > 2 else None
    # optional extra argument (used by some solvers, e.g. D for 'expand')
    extra_arg = sys.argv[3] if len(sys.argv) > 3 else None

    # registry of available methods: name -> (callable to solve one instance, description)
    def _run_dynamic(coverage_sets, A, inst):
        solver = dynamic_mod.DPSolver(coverage_sets, len(inst.rectangles))
        return solver.solve() or []

    def _run_greedy(coverage_sets, A, inst):
        solver = greedy_mod.GreedySolver(A)
        return solver.solve() or []

    def _run_integer(coverage_sets, A, inst):
        solver = integer_mod.IntegerSolver(A)
        return solver.solve() or []

    def _run_csp(coverage_sets, A, inst):
        sol = csp_mod.MACSolver(A).solve()
        if sol is None:
            return []
        # sol may be a list of 0/1 selection per vertex
        return [i for i, v in enumerate(sol) if v == 1]

    def _run_coloring(coverage_sets, A, inst):

        guards = _run_integer(coverage_sets, A, inst)

        if extensions_mod is None:
            return guards

        try:

            graph = extensions_mod.build_conflict_graph(
                guards,
                A
            )

            coloring, num_colors = extensions_mod.exact_coloring(graph)

            print("\nOptimal guard coloring:")

            for g in guards:
                print(f"Guard {g} -> color {coloring[g]}")

            print(f"\nMinimum number of colors: {num_colors}")

            return guards

        except Exception as e:

            print("Coloring error:", e)

            return guards

    def _run_expand(coverage_sets, A, inst, D=1):

        if extensions_mod is None:
            return []

        try:

            expanded_coverage = (
                extensions_mod.build_expanded_coverage_sets(inst, D)
            )

            # rebuild matrix using expanded coverage
            expanded_A = [
                [0 for _ in inst.rectangles]
                for _ in inst.vertices
            ]

            for vi, cov in enumerate(expanded_coverage):

                for r in cov:
                    expanded_A[vi][r] = 1

            # solve using expanded visibility
            solver = integer_mod.IntegerSolver(expanded_A)

            return solver.solve() or []

        except Exception as e:

            print("Expand solver error:", e)

            return []

    SOLVERS = {
        'dynamic': (
            _run_dynamic,
            'Exact DP set-cover solver'
        ),

        'greedy': (
            _run_greedy,
            'Greedy heuristic (fast, non-optimal)'
        ),

        'integer': (
            _run_integer,
            'Exact ILP set-cover solver'
        ),

        'csp': (
            _run_csp,
            'Backtracking CSP with MAC'
        ),

        'coloring': (
            _run_coloring,
            'Optimal graph coloring of guards'
        ),

        'expand': (
            _run_expand,
            'Extended-visibility set cover (distance D)'
        ),
    }

    instances = parse_instances(fname)

    # choose method
    method = method_arg
    if method is None:
        print('Available solvers:')
        for i, (name, v) in enumerate(SOLVERS.items(), start=1):
            print(f"{i}. {name} - {v[1]}")

        choice = input('Choose solver by name or number: ').strip()
        if choice.isdigit():
            idx = int(choice) - 1
            names = list(SOLVERS.keys())
            if 0 <= idx < len(names):
                method = names[idx]
        else:
            method = choice

    if method not in SOLVERS:
        print(f"Unknown solver '{method}'. Available: {', '.join(SOLVERS.keys())}")
        sys.exit(1)

    solver_runner = SOLVERS[method][0]

    # If expand selected and no extra_arg provided, ask the user for D interactively
    if method == 'expand' and extra_arg is None:
        try:
            ans = input('Enter expansion distance D (integer, default 1): ').strip()
        except Exception:
            ans = ''
        if ans == '':
            extra_arg = '1'
        else:
            try:
                _ = int(ans)
                extra_arg = ans
            except Exception:
                print('Invalid D, using default 1')
                extra_arg = '1'

    out = []

    for inst_idx, inst in enumerate(instances, start=1):

        coverage_sets, vertices = build_coverage_sets(inst)

        # also build coverage matrix A (vertices x rectangles) for solvers that expect it
        A = [[0 for _ in inst.rectangles] for _ in vertices]
        for vi, cov in enumerate(coverage_sets):
            for r in cov:
                A[vi][r] = 1

        # call solver AFTER matrix is complete
        if method == 'expand':
            try:
                D = int(extra_arg) if extra_arg is not None else 1
            except ValueError:
                D = 1

            guards = solver_runner(coverage_sets, A, inst, D) or []

        else:
            guards = solver_runner(coverage_sets, A, inst) or []

        guard_coords = [[vertices[g][0], vertices[g][1]] for g in guards]

        rects = [
            {'id': r.id, 'vertices': [[x, y] for (x, y) in r.vertices]}
            for r in inst.rectangles
        ]

        out.append({
            'instance': inst_idx,
            'k': inst.k,
            'rectangles': rects,
            'method': method,
            'guards_indices': guards,
            'guards_coords': guard_coords
        })

    # print JSON once
    #print(json.dumps(out, indent=2))

    # concise plain output
    for inst_out in out:
        print(f"Instance {inst_out['instance']} (method={inst_out['method']})")
        print('Guard vertices:')
        for x, y in inst_out['guards_coords']:
            print(f"{x} {y}")
        print(f"Total guards: {len(inst_out['guards_coords'])}")
        print()