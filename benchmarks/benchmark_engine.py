
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
        capture_output: bool = False,
    ):
        self.workload_path = Path(workload_path)
        self.warmup_runs = warmup_runs
        self.benchmark_runs = benchmark_runs
        self.capture_output = capture_output

    def run(self) -> dict:
        """Execute the workload and return benchmark results."""

        if not self.workload_path.exists():
            raise FileNotFoundError(
                f"Workload not found: {self.workload_path}"
            )

        if self.workload_path.suffix != ".py":
            raise ValueError("Currently only Python workloads are supported.")

        if self.warmup_runs < 0 or self.benchmark_runs < 1:
            raise ValueError("Invalid warmup or benchmark run count.")

        source = self.workload_path.read_text(encoding="utf-8")
        namespace = {"__name__": "__benchmark__"}

        exec(compile(source, str(self.workload_path), "exec"), namespace)

        if "run_workload" not in namespace:
            raise ValueError(
                "Workload must define a run_workload() function."
            )

        run_workload = namespace["run_workload"]

        for _ in range(self.warmup_runs):
            run_workload()

        execution_times = []
        last_output = None

        for _ in range(self.benchmark_runs):
            start = time.perf_counter()
            output = run_workload()
            end = time.perf_counter()

            execution_times.append(end - start)

            if self.capture_output:
                last_output = output

        result = {
            "workload": self.workload_path.name,
            "warmup_runs": self.warmup_runs,
            "benchmark_runs": self.benchmark_runs,
            "execution_times_seconds": execution_times,
            "average_time_seconds": statistics.mean(execution_times),
            "minimum_time_seconds": min(execution_times),
            "maximum_time_seconds": max(execution_times),
        }

        if self.capture_output:
            result["output"] = last_output

        return result
