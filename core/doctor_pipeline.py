from pathlib import Path

from agents.governed_action import GovernedOptimizationAction
from agents.correctness_engine import CorrectnessEngine
from agents.optimization_detector import OptimizationDetector
from agents.verification_engine import VerificationEngine
from agents.workload_analyzer import WorkloadAnalyzer
from benchmarks.benchmark_engine import BenchmarkEngine
from benchmarks.result_store import BenchmarkResultStore
from core.safe_execution import SafeFileExecutor


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
        Execute
            ↓
        Benchmark
            ↓
        Verify
            ↓
        Accept / Rollback
            ↓
        Report

    The analysis workload and benchmark workload can be different
    during local integration testing.
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
        self.correctness_engine = CorrectnessEngine()
        self.result_store = BenchmarkResultStore()
        self.safe_executor = SafeFileExecutor()

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

    def benchmark(self, capture_output: bool = False) -> dict:
        engine = BenchmarkEngine(
            self.benchmark_workload_path,
            warmup_runs=2,
            benchmark_runs=5,
            capture_output=capture_output,
        )
        return engine.run()

    def verify(
        self,
        before: dict,
        after: dict,
        correctness_passed: bool = False,
        reference_output=None,
        candidate_output=None,
    ) -> dict:
        """Verify correctness and performance before accepting a candidate."""

        if (reference_output is None) != (candidate_output is None):
            raise ValueError(
                "Provide both reference_output and candidate_output."
            )

        if reference_output is not None:
            correctness_result = self.correctness_engine.compare(
                reference_output,
                candidate_output,
            )
        else:
            correctness_result = {
                "passed": bool(correctness_passed),
                "mismatch_count": None,
                "mismatches": [],
            }

        result = self.verifier.verify(
            before_benchmark=before,
            after_benchmark=after,
            correctness_result=correctness_result,
        )

        result["correctness_result"] = correctness_result

        return result

    def execute_optimization(
        self,
        action: GovernedOptimizationAction,
        new_content: str,
        before_benchmark: dict,
        reference_output,
    ) -> dict:
        """
        Apply an approved optimization, verify it, and rollback on failure.
        """

        execution = self.safe_executor.execute(
            action=action,
            target_path=self.workload_path,
            new_content=new_content,
        )

        backup_path = execution["backup_path"]

        try:
            after_benchmark = BenchmarkEngine(
                self.workload_path,
                warmup_runs=2,
                benchmark_runs=5,
                capture_output=True,
            ).run()

            candidate_output = after_benchmark.get("output")

            verification = self.verify(
                before=before_benchmark,
                after=after_benchmark,
                reference_output=reference_output,
                candidate_output=candidate_output,
            )

            action.record_benchmark(
                before_benchmark,
                after_benchmark,
            )

            action.record_verification(verification)

            if verification.get("verified", False):
                action.accept()

                return {
                    "status": "accepted",
                    "execution": execution,
                    "benchmark": after_benchmark,
                    "verification": verification,
                    "action": action.to_dict(),
                }

            rollback = self.safe_executor.rollback(
                action=action,
                target_path=self.workload_path,
                backup_path=backup_path,
                reason=(
                    "Optimization failed correctness or "
                    "performance verification."
                ),
            )

            return {
                "status": "rolled_back",
                "execution": execution,
                "benchmark": after_benchmark,
                "verification": verification,
                "rollback": rollback,
                "action": action.to_dict(),
            }

        except Exception:
            if Path(backup_path).is_file():
                self.safe_executor.rollback(
                    action=action,
                    target_path=self.workload_path,
                    backup_path=backup_path,
                    reason="Optimization execution failed.",
                )
            raise

    def save_result(self, result: dict, filename: str):
        return self.result_store.save(result, filename)
