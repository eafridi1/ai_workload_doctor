from agents.governed_action import GovernedOptimizationAction
from agents.optimization_detector import OptimizationDetector
from agents.verification_engine import VerificationEngine
from agents.workload_analyzer import WorkloadAnalyzer
from benchmarks.benchmark_engine import BenchmarkEngine
from benchmarks.result_store import BenchmarkResultStore


class WorkloadDoctorPipeline:
    """
    Connect the deterministic components of AI Workload Doctor.

    Current pipeline:

        Analyze
            ↓
        Detect
            ↓
        Govern
            ↓
        Benchmark
            ↓
        Verify
            ↓
        Report

    The analysis workload and benchmark workload can be different
    during local integration testing.

    This version does not modify workload code automatically.
    """

    def __init__(
        self,
        workload_path: str,
        benchmark_workload_path: str | None = None,
    ):
        self.workload_path = workload_path
        self.benchmark_workload_path = (
            benchmark_workload_path or workload_path
        )

        self.analyzer = WorkloadAnalyzer(workload_path)
        self.detector = OptimizationDetector()
        self.verifier = VerificationEngine()
        self.result_store = BenchmarkResultStore()

    def analyze(self) -> dict:
        return self.analyzer.analyze()

    def detect_candidates(self, analysis: dict) -> list[dict]:
        return self.detector.detect(analysis)

    def create_action(
        self,
        candidate: dict,
        action_id: str,
    ) -> GovernedOptimizationAction:
        return GovernedOptimizationAction(
            action_id=action_id,
            candidate=candidate["candidate"],
            category=candidate["category"],
            reason=candidate["reason"],
            evidence=candidate["evidence"],
            requires_human_approval=candidate["requires_human_approval"],
            verification_required=candidate["verification_required"],
        )

    def benchmark(self) -> dict:
        engine = BenchmarkEngine(
            self.benchmark_workload_path,
            warmup_runs=2,
            benchmark_runs=5,
        )
        return engine.run()

    def verify(
        self,
        before: dict,
        after: dict,
        correctness_passed: bool = True,
    ) -> dict:
        correctness_result = {
            "passed": correctness_passed,
        }

        return self.verifier.verify(
            before_benchmark=before,
            after_benchmark=after,
            correctness_result=correctness_result,
        )

    def save_result(self, result: dict, filename: str):
        return self.result_store.save(result, filename)
