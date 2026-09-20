import statistics
import time
from pathlib import Path


class BenchmarkEngine:
    """Measure execution time for a Python workload."""

    def __init__(
        self,
        workload_path: str,
        warmup_runs: int = 2,
        benchmark_runs: int = 5,
    ):
        self.workload_path = Path(workload_path)
        self.warmup_runs = warmup_runs
        self.benchmark_runs = benchmark_runs

    def run(self) -> dict:
        """Execute the workload and return benchmark results."""

        if not self.workload_path.exists():
            raise FileNotFoundError(
                f"Workload not found: {self.workload_path}"
            )

        if self.workload_path.suffix != ".py":
            raise ValueError("Currently only Python workloads are supported.")

        source = self.workload_path.read_text(encoding="utf-8")

        namespace = {
            "__name__": "__benchmark__",
        }

        # Load the workload without triggering its __main__ block.
        exec(compile(source, str(self.workload_path), "exec"), namespace)

        if "run_workload" not in namespace:
            raise ValueError(
                "Workload must define a run_workload() function."
            )

        run_workload = namespace["run_workload"]

        # Warmup runs are not included in benchmark measurements.
        for _ in range(self.warmup_runs):
            run_workload()

        execution_times = []

        for _ in range(self.benchmark_runs):
            start = time.perf_counter()

            run_workload()

            end = time.perf_counter()
            execution_times.append(end - start)

        average_time = statistics.mean(execution_times)
        minimum_time = min(execution_times)
        maximum_time = max(execution_times)

        return {
            "workload": self.workload_path.name,
            "warmup_runs": self.warmup_runs,
            "benchmark_runs": self.benchmark_runs,
            "execution_times_seconds": execution_times,
            "average_time_seconds": average_time,
            "minimum_time_seconds": minimum_time,
            "maximum_time_seconds": maximum_time,
        }
