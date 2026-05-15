# this file is used to calculate average performance times of the algorithms

import time
from statistics import mean
import multiprocessing as mp

from parse import parse_instances, build_coverage_sets

import dynamic as dynamic_mod
import greedy as greedy_mod
import integer_solver as integer_mod
import csp_mac as csp_mod

TIME_LIMIT = 60


# WRAPPERS
def run_dynamic(coverage_sets, A, inst):
    solver = dynamic_mod.DPSolver(coverage_sets, len(inst.rectangles))
    return solver.solve() or []


def run_greedy(coverage_sets, A, inst):
    solver = greedy_mod.GreedySolver(A)
    return solver.solve() or []


def run_integer(coverage_sets, A, inst):
    solver = integer_mod.IntegerSolver(A)
    return solver.solve() or []


def run_csp(coverage_sets, A, inst):
    sol = csp_mod.MACSolver(A).solve()
    if sol is None:
        return []
    # sol may be a list of 0/1 selection per vertex
    return [i for i, v in enumerate(sol) if v == 1]


SOLVERS = {
    "dynamic": run_dynamic,
    "greedy": run_greedy,
    "integer": run_integer,
    "csp": run_csp,
}


# timed solver
def time_solver(solver_func, coverage_sets, A, i, queue):
    try:
        result = solver_func(coverage_sets, A, i)
        queue.put(("ok", result))
    except Exception as e:
        queue.put(("err", repr(e)))


def benchmark_one(solver_func, coverage_sets, A, i):
    queue = mp.Queue()
    p = mp.Process(target=time_solver, args=(solver_func, coverage_sets, A, i, queue))

    start = time.perf_counter()

    p.start()
    p.join(TIME_LIMIT)

    if p.is_alive():
        p.terminate()
        p.join()
        return None  # TLE

    end = time.perf_counter()
    return end - start


# main benchmarking functions
def benchmarker(instances, solver_func, runs=2):
    instance_times = []

    try:
        for _ in range(runs):
            for i in instances:
                coverage_sets, vertices = build_coverage_sets(i)

                # coverage matrix
                A = [[0 for _ in i.rectangles] for _ in vertices]

                for vi, cov in enumerate(coverage_sets):
                    for r in cov:
                        A[vi][r] = 1

                t = benchmark_one(solver_func, coverage_sets, A, i)
                if t is None:
                    return None

                instance_times.append(t)

        return mean(instance_times)
    except TimeoutError:
        return None


def main():
    files = [
        "example_inputs/10rect_5instances",
        "example_inputs/30rect_5instances",
        "example_inputs/50rect_5instances",
    ]

    output_file = "benchmark_results.txt"

    with open(output_file, "w") as f:
        for input_file in files:
            print(f"Processing file: {input_file}..")

            instances = parse_instances(input_file)
            results = {}

            f.write(f"==== {input_file} ====\n")
            for name, solver in SOLVERS.items():
                print(f"Running {name}..")

                avgTime = benchmarker(instances, solver, runs=2)

                if avgTime is None:
                    f.write(f"{name}: time limit exceeded ({TIME_LIMIT} seconds)\n")
                else:
                    f.write(f"{name}: {avgTime:.6f} seconds\n")

                results[name] = avgTime

            f.write("\n")

    print(f"Results written to {output_file}")


if __name__ == "__main__":
    main()
