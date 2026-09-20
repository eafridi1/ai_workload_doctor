import json
from pathlib import Path


class BenchmarkResultStore:
    """Save and compare benchmark results."""

    def __init__(self, results_directory: str = "reports"):
        self.results_directory = Path(results_directory)
        self.results_directory.mkdir(parents=True, exist_ok=True)

    def save(self, result: dict, filename: str) -> Path:
        """Save a benchmark result as JSON."""

        output_path = self.results_directory / filename

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        return output_path

    @staticmethod
    def compare(before: dict, after: dict) -> dict:
        """Compare two benchmark results."""

        before_time = before["average_time_seconds"]
        after_time = after["average_time_seconds"]

        difference = before_time - after_time

        if before_time > 0:
            improvement_percent = (
                difference / before_time
            ) * 100
        else:
            improvement_percent = 0.0

        return {
            "workload": after["workload"],
            "before_average_seconds": before_time,
            "after_average_seconds": after_time,
            "difference_seconds": difference,
            "improvement_percent": improvement_percent,
            "faster": after_time < before_time,
        }
