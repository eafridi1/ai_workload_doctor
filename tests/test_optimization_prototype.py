
import unittest

from agents.correctness_engine import CorrectnessEngine
from benchmarks.benchmark_engine import BenchmarkEngine
from benchmarks.result_store import BenchmarkResultStore


class TestOptimizationPrototype(unittest.TestCase):

    def test_optimized_output_matches_reference(self):
        correctness = CorrectnessEngine()

        from workloads.optimization_reference import sum_squares as reference
        from workloads.optimization_candidate import sum_squares as candidate

        test_values = [0, 1, 2, 10, 100, 1000, 500_000]

        for n in test_values:
            with self.subTest(n=n):
                result = correctness.compare(
                    reference(n),
                    candidate(n),
                )
                self.assertTrue(
                    result["passed"],
                    msg=f"Mismatch for n={n}: {result['mismatches']}",
                )

    def test_benchmark_both_implementations(self):
        reference_engine = BenchmarkEngine(
            "workloads/optimization_reference.py",
            warmup_runs=2,
            benchmark_runs=5,
        )

        candidate_engine = BenchmarkEngine(
            "workloads/optimization_candidate.py",
            warmup_runs=2,
            benchmark_runs=5,
        )

        before = reference_engine.run()
        after = candidate_engine.run()

        comparison = BenchmarkResultStore.compare(before, after)

        print("\n--- Optimization Benchmark ---")
        print(f"Reference average: {before['average_time_seconds']:.6f}s")
        print(f"Candidate average: {after['average_time_seconds']:.6f}s")
        print(f"Measured improvement: {comparison['improvement_percent']:.2f}%")
        print(f"Candidate faster: {comparison['faster']}")

        # Check that benchmark measurements were produced.
        self.assertEqual(before["benchmark_runs"], 5)
        self.assertEqual(after["benchmark_runs"], 5)
        self.assertGreater(before["average_time_seconds"], 0)
        self.assertGreater(after["average_time_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
