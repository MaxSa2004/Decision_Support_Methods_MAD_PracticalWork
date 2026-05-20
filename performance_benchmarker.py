"""Benchmark unificado para cobertura parcial com subconjuntos aleatorios.

Este script pode correr:
- solvers base (dynamic, greedy, integer, csp)
- extensoes (coloring, expand)
- ambos no mesmo run
"""

import argparse
import multiprocessing as mp
import random
import time
from statistics import mean

from main import build_coverage_sets, parse_instances

import csp_mac as csp_mod
import dynamic as dynamic_mod
import extensions as extensions_mod
import greedy as greedy_mod
import integer_solver as integer_mod

TIME_LIMIT = 60


def build_matrix(instance):
    coverage_sets, vertices = build_coverage_sets(instance)

    A = [[0 for _ in instance.rectangles] for _ in vertices]
    for vi, cov in enumerate(coverage_sets):
        for r in cov:
            A[vi][r] = 1

    return coverage_sets, A


def generate_required_subset(n_rectangles, ratio, rng):
    if ratio <= 0 or ratio > 1:
        raise ValueError("All ratios must be in (0, 1].")

    k = max(1, min(n_rectangles, int(round(ratio * n_rectangles))))
    if k == n_rectangles:
        return list(range(n_rectangles))
    return sorted(rng.sample(range(n_rectangles), k))


# Base solvers
def run_dynamic(coverage_sets, A, inst, required, expand_distance):
    solver = dynamic_mod.DPSolver(
        coverage_sets,
        len(inst.rectangles),
        required=required,
    )
    solution = solver.solve() or []
    return {"guards": len(solution)}


def run_greedy(coverage_sets, A, inst, required, expand_distance):
    solver = greedy_mod.GreedySolver(A, required=required)
    solution = solver.solve() or []
    return {"guards": len(solution)}


def run_integer(coverage_sets, A, inst, required, expand_distance):
    solver = integer_mod.IntegerSolver(A, required=required)
    solution = solver.solve() or []
    return {"guards": len(solution)}


def run_csp(coverage_sets, A, inst, required, expand_distance):
    solution = csp_mod.MACSolver(A, required=required).solve()
    if solution is None:
        return {"guards": 0}
    selected = [i for i, v in enumerate(solution) if v == 1]
    return {"guards": len(selected)}


# Extension solvers
def run_coloring(coverage_sets, A, inst, required, expand_distance):
    guards = integer_mod.IntegerSolver(A, required=required).solve() or []

    # Consider only required rectangles when building conflicts for partial coverage.
    required_A = [[row[j] for j in required] for row in A]
    graph = extensions_mod.build_conflict_graph(guards, required_A)
    _, num_colors = extensions_mod.exact_coloring(graph)

    return {
        "guards": len(guards),
        "colors": int(num_colors),
    }


def run_expand(coverage_sets, A, inst, required, expand_distance):
    expanded_coverage = extensions_mod.build_expanded_coverage_sets(inst, expand_distance)

    expanded_A = [[0 for _ in inst.rectangles] for _ in inst.vertices]
    for vi, cov in enumerate(expanded_coverage):
        for r in cov:
            expanded_A[vi][r] = 1

    guards = integer_mod.IntegerSolver(expanded_A, required=required).solve() or []
    return {"guards": len(guards)}


BASE_SOLVERS = {
    "dynamic": run_dynamic,
    "greedy": run_greedy,
    "integer": run_integer,
    "csp": run_csp,
}

EXT_SOLVERS = {
    "coloring": run_coloring,
    "expand": run_expand,
}


def parse_csv_names(raw):
    return [p.strip() for p in raw.split(",") if p.strip()]


def parse_ratios(raw_ratios):
    return [float(p.strip()) for p in raw_ratios.split(",") if p.strip()]


def build_tasks_for_ratio(instance_data, ratio, samples_per_ratio, rng):
    tasks = []
    required_sizes = []

    for _ in range(samples_per_ratio):
        for inst, coverage_sets, A in instance_data:
            required = generate_required_subset(len(inst.rectangles), ratio, rng)
            required_sizes.append(len(required))
            tasks.append((coverage_sets, A, inst, required))

    return tasks, mean(required_sizes) if required_sizes else 0


def time_solver(solver_func, coverage_sets, A, inst, required, expand_distance, queue):
    try:
        metrics = solver_func(coverage_sets, A, inst, required, expand_distance)
        queue.put(("ok", metrics))
    except Exception as e:
        queue.put(("err", repr(e)))


def benchmark_one(solver_func, coverage_sets, A, inst, required, expand_distance):
    queue = mp.Queue()
    p = mp.Process(
        target=time_solver,
        args=(solver_func, coverage_sets, A, inst, required, expand_distance, queue),
    )

    start = time.perf_counter()
    p.start()
    p.join(TIME_LIMIT)

    if p.is_alive():
        p.terminate()
        p.join()
        return None

    end = time.perf_counter()

    if queue.empty():
        return None

    status, payload = queue.get()
    if status != "ok":
        return None

    return end - start, payload


def aggregate_metrics(metric_list):
    out = {}
    if not metric_list:
        return out

    keys = metric_list[0].keys()
    for k in keys:
        out[f"avg_{k}"] = mean(m[k] for m in metric_list)
    return out


def benchmark_tasks(solver_func, tasks, repetitions=1, expand_distance=1):
    times = []
    metrics = []

    for _ in range(repetitions):
        for coverage_sets, A, inst, required in tasks:
            result = benchmark_one(
                solver_func,
                coverage_sets,
                A,
                inst,
                required,
                expand_distance,
            )
            if result is None:
                return None

            elapsed, payload = result
            times.append(elapsed)
            metrics.append(payload)

    agg = aggregate_metrics(metrics)
    agg["avg_time"] = mean(times)
    agg["samples"] = len(times)
    return agg


def format_result_line(name, result):
    line = f"{name}: avg_time={result['avg_time']:.6f}s"
    if "avg_guards" in result:
        line += f", avg_guards={result['avg_guards']:.3f}"
    if "avg_colors" in result:
        line += f", avg_colors={result['avg_colors']:.3f}"
    line += f", samples={result['samples']}"
    return line


def pick_solvers(args):
    selected = {}

    if args.suite in ("base", "all"):
        base_names = parse_csv_names(args.base_solvers)
        for name in base_names:
            if name not in BASE_SOLVERS:
                raise ValueError(f"Unknown base solver: {name}")
            selected[name] = BASE_SOLVERS[name]

    if args.suite in ("extensions", "all"):
        ext_names = parse_csv_names(args.extensions)
        for name in ext_names:
            if name not in EXT_SOLVERS:
                raise ValueError(f"Unknown extension solver: {name}")
            selected[name] = EXT_SOLVERS[name]

    if not selected:
        raise ValueError("No solvers selected.")

    return selected


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark unificado de cobertura parcial para base e extensoes.",
    )
    parser.add_argument(
        "--suite",
        choices=["base", "extensions", "all"],
        default="all",
        help="Escolhe que familia de solvers executar.",
    )
    parser.add_argument(
        "--base-solvers",
        default="dynamic,greedy,integer,csp",
        help="Solvers base (CSV) a executar quando suite inclui base.",
    )
    parser.add_argument(
        "--extensions",
        default="coloring,expand",
        help="Extensoes (CSV) a executar quando suite inclui extensions.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        default=[
            "example_inputs/10rect_5instances",
            "example_inputs/30rect_5instances",
            "example_inputs/50rect_5instances",
            "example_inputs/100rect_5instances",
            "example_inputs/500rect_5instances",
            "example_inputs/1000rect_5instances",
        ],
        help="Ficheiros de instancias para testar.",
    )
    parser.add_argument(
        "--ratios",
        default="0.1,0.25,0.5,0.75,1.0",
        help="Lista de racios de cobertura obrigatoria em [0,1], separados por virgula.",
    )
    parser.add_argument(
        "--samples-per-ratio",
        type=int,
        default=3,
        help="Numero de subconjuntos aleatorios por ratio, por instancia.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="Repeticoes de cada tarefa para media temporal.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed do gerador aleatorio para reprodutibilidade.",
    )
    parser.add_argument(
        "--expand-distance",
        type=int,
        default=3,
        help="Distancia D usada na extensao expand.",
    )
    parser.add_argument(
        "--output",
        default="benchmark_partial_results.txt",
        help="Ficheiro de saida.",
    )

    args = parser.parse_args()
    ratios = parse_ratios(args.ratios)
    rng = random.Random(args.seed)
    selected_solvers = pick_solvers(args)
    active_solvers = dict(selected_solvers)
    disabled_solvers = {}

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("Benchmark unificado de cobertura parcial\n")
        f.write(f"suite={args.suite}\n")
        f.write(f"solvers={','.join(selected_solvers.keys())}\n")
        f.write(f"TIME_LIMIT={TIME_LIMIT}s\n")
        f.write(f"seed={args.seed}\n")
        f.write(f"ratios={ratios}\n")
        f.write(f"samples_per_ratio={args.samples_per_ratio}\n")
        f.write(f"repetitions={args.repetitions}\n")
        f.write(f"expand_distance={args.expand_distance}\n\n")

        for input_file in args.files:
            print(f"Processing file: {input_file}...")
            instances = parse_instances(input_file)

            instance_data = []
            for inst in instances:
                coverage_sets, A = build_matrix(inst)
                instance_data.append((inst, coverage_sets, A))

            f.write(f"==== {input_file} ====\n")

            for ratio in ratios:
                print(f"  Ratio {ratio:.2f}...")

                tasks, avg_required_size = build_tasks_for_ratio(
                    instance_data,
                    ratio,
                    args.samples_per_ratio,
                    rng,
                )

                f.write(
                    f"-- required_ratio={ratio:.2f} "
                    f"(avg_required_rectangles={avg_required_size:.2f}) --\n"
                )

                if not active_solvers:
                    f.write("all solvers disabled after timeout/error in previous iterations\n\n")
                    continue

                for name, solver in list(active_solvers.items()):
                    print(f"    Running {name}...")
                    result = benchmark_tasks(
                        solver,
                        tasks,
                        repetitions=args.repetitions,
                        expand_distance=args.expand_distance,
                    )

                    if result is None:
                        f.write(
                            f"{name}: time limit exceeded/error "
                            f"({TIME_LIMIT} seconds)\n"
                        )
                        disabled_solvers[name] = "timeout/error"
                        del active_solvers[name]
                        f.write(f"{name}: disabled for all next iterations\n")
                    else:
                        f.write(format_result_line(name, result) + "\n")

                f.write("\n")

            f.write("\n")

        if disabled_solvers:
            f.write("disabled_solvers=\n")
            for name, reason in disabled_solvers.items():
                f.write(f"- {name}: {reason}\n")

    print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()
