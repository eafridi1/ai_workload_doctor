from benchmarks.benchmark_engine import BenchmarkEngine
from benchmarks.result_store import BenchmarkResultStore


def main():
    benchmark = BenchmarkEngine(
        "workloads/benchmark_workload.py",
        warmup_runs=2,
        benchmark_runs=5,
    )

    result = benchmark.run()

    store = BenchmarkResultStore()

    output_path = store.save(
        result,
        "baseline_benchmark.json",
    )

    comparison = store.compare(result, result)

    print("=" * 60)
    print("AMD AI WORKLOAD DOCTOR")
    print("BENCHMARK RESULT STORAGE")
    print("=" * 60)

    print(f"saved_to: {output_path}")
    print(f"workload: {result['workload']}")
    print(
        f"average_time_seconds: "
        f"{result['average_time_seconds']}"
    )

    print("=" * 60)
    print("COMPARISON TEST")
    print("=" * 60)

    for key, value in comparison.items():
        print(f"{key}: {value}")

    print("=" * 60)


if __name__ == "__main__":
    main()
