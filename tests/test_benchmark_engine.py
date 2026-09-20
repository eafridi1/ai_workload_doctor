from benchmarks.benchmark_engine import BenchmarkEngine


def main():
    benchmark = BenchmarkEngine(
        "workloads/benchmark_workload.py",
        warmup_runs=2,
        benchmark_runs=5,
    )

    result = benchmark.run()

    print("=" * 60)
    print("AMD AI WORKLOAD DOCTOR")
    print("BASELINE BENCHMARK")
    print("=" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("=" * 60)


if __name__ == "__main__":
    main()
