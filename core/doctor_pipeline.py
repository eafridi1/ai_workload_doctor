from pathlib import Path

from agents.governed_action import GovernedOptimizationAction
from agents.correctness_engine import CorrectnessEngine
from agents.optimization_detector import OptimizationDetector
from agents.verification_engine import VerificationEngine
from agents.workload_analyzer import WorkloadAnalyzer
from benchmarks.benchmark_engine import BenchmarkEngine
from benchmarks.result_store import BenchmarkResultStore
from core.safe_execution import SafeFileExecutor
from ssor.case_record import CaseRecord
from ssor.case_store import CaseStore
from ssor.provenance import create_provenance


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
        Report / SSoR

    The analysis workload and benchmark workload can be different
    during local integration testing.
    """

    def __init__(
        self,
        workload_path: str,
        benchmark_workload_path: str | None = None,
        case_id: str | None = None,
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

        self.case_store = CaseStore()

        self.case = CaseRecord(
            case_id=case_id or "local-case",
            workload=workload_path,
        )

    def analyze(self) -> dict:
        result = self.analyzer.analyze()

        self.case.analysis = result
        self.case.add_provenance(
            create_provenance(
                source="workload_analyzer",
                source_type="system",
                details={
                    "workload": self.workload_path,
                },
            )
        )
        self.case.record_event(
            "analysis_completed",
            {
                "workload": self.workload_path,
            },
        )

        return result

    def detect_candidates(self, analysis: dict) -> list[dict]:
        candidates = self.detector.detect(analysis)

        if candidates:
            self.case.candidate = candidates[0]

        self.case.record_event(
            "candidates_detected",
            {
                "count": len(candidates),
            },
        )

        return candidates

    def create_action(
        self,
        candidate: dict,
        action_id: str,
    ) -> GovernedOptimizationAction:
        action = GovernedOptimizationAction(
            action_id=action_id,
            candidate=candidate["candidate"],
            category=candidate["category"],
            reason=candidate["reason"],
            evidence=candidate["evidence"],
            requires_human_approval=candidate[
                "requires_human_approval"
            ],
            verification_required=candidate[
                "verification_required"
            ],
        )

        self.case.candidate = candidate
        self.case.approval = {
            "required": action.requires_human_approval,
            "approved": action.human_approved,
        }

        self.case.record_event(
            "governed_action_created",
            {
                "action_id": action_id,
                "approval_required": (
                    action.requires_human_approval
                ),
            },
        )

        return action

    def benchmark(self, capture_output: bool = False) -> dict:
        engine = BenchmarkEngine(
            self.benchmark_workload_path,
            warmup_runs=2,
            benchmark_runs=5,
            capture_output=capture_output,
        )

        result = engine.run()

        self.case.benchmarks["latest"] = result

        self.case.add_provenance(
            create_provenance(
                source="benchmark_engine",
                source_type="system",
                details={
                    "workload": self.benchmark_workload_path,
                },
            )
        )

        return result

    def verify(
        self,
        before: dict,
        after: dict,
        correctness_passed: bool = False,
        reference_output=None,
        candidate_output=None,
    ) -> dict:
        """Verify correctness and performance before accepting a candidate."""

        if (reference_output is None) != (
            candidate_output is None
        ):
            raise ValueError(
                "Provide both reference_output and candidate_output."
            )

        if reference_output is not None:
            correctness_result = (
                self.correctness_engine.compare(
                    reference_output,
                    candidate_output,
                )
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

        self.case.verification = result

        self.case.record_event(
            "verification_completed",
            {
                "verified": result.get(
                    "verified",
                    False,
                ),
                "decision": result.get(
                    "decision",
                ),
            },
        )

        return result

    def execute_optimization(
        self,
        action: GovernedOptimizationAction,
        new_content: str,
        before_benchmark: dict,
        reference_output,
    ) -> dict:
        """
        Apply an approved optimization, verify it,
        and rollback on failure.
        """

        self.case.approval = {
            "required": action.requires_human_approval,
            "approved": action.human_approved,
        }

        execution = self.safe_executor.execute(
            action=action,
            target_path=self.workload_path,
            new_content=new_content,
        )

        self.case.execution = execution

        self.case.record_event(
            "optimization_executed",
            {
                "target": self.workload_path,
            },
        )

        backup_path = execution["backup_path"]

        try:
            after_benchmark = BenchmarkEngine(
                self.workload_path,
                warmup_runs=2,
                benchmark_runs=5,
                capture_output=True,
            ).run()

            candidate_output = after_benchmark.get(
                "output"
            )

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

            action.record_verification(
                verification
            )

            self.case.benchmarks = {
                "before": before_benchmark,
                "after": after_benchmark,
            }

            if verification.get(
                "verified",
                False,
            ):
                action.accept()

                self.case.outcome = "accepted"

                self.case.record_event(
                    "optimization_accepted"
                )

                case_path = self.case_store.save(
                    self.case
                )

                return {
                    "status": "accepted",
                    "execution": execution,
                    "benchmark": after_benchmark,
                    "verification": verification,
                    "action": action.to_dict(),
                    "ssor": {
                        "case_id": self.case.case_id,
                        "path": case_path,
                    },
                }

            rollback = self.safe_executor.rollback(
                action=action,
                target_path=self.workload_path,
                backup_path=backup_path,
                reason=(
                    "Optimization failed correctness "
                    "or performance verification."
                ),
            )

            self.case.outcome = "rolled_back"

            self.case.record_event(
                "optimization_rolled_back",
                {
                    "reason": (
                        "correctness_or_performance_failure"
                    ),
                },
            )

            case_path = self.case_store.save(
                self.case
            )

            return {
                "status": "rolled_back",
                "execution": execution,
                "benchmark": after_benchmark,
                "verification": verification,
                "rollback": rollback,
                "action": action.to_dict(),
                "ssor": {
                    "case_id": self.case.case_id,
                    "path": case_path,
                },
            }

        except Exception:
            if Path(backup_path).is_file():
                self.safe_executor.rollback(
                    action=action,
                    target_path=self.workload_path,
                    backup_path=backup_path,
                    reason="Optimization execution failed.",
                )

            self.case.outcome = "error"

            self.case.record_event(
                "optimization_error"
            )

            self.case_store.save(self.case)

            raise

    def save_case(self) -> str:
        """Persist the current SSoR case."""

        return self.case_store.save(
            self.case
        )
    def load_case(self, case_id: str) -> dict:
        """Recover a saved SSoR case for handoff or review."""

        self.case = self.case_store.load(case_id)

        self.case.record_event(
            "case_recovered",
            {
                "recovered_by": "WorkloadDoctorPipeline",
            },
        )

        return self.case.to_dict()


    def save_result(
        self,
        result: dict,
        filename: str,
    ):
        return self.result_store.save(
            result,
            filename,
        )
