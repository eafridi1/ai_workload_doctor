class OptimizationDetector:
    """
    Detect possible optimization opportunities.

    The detector produces candidates, not automatic decisions.

    4D principles:
    - Description: describe observed workload characteristics.
    - Delegation: identify work suitable for specialized components.
    - Discernment: separate evidence from hypotheses.
    - Diligence: require testing and verification before acceptance.

    Human-in-the-loop:
    Significant optimization actions require human approval.

    10/80/10:
    This is a design target, not a scientific law:
    - 10% human direction
    - 80% agent execution
    - 10% human review
    """

    def detect(self, analysis: dict) -> list[dict]:
        candidates = []

        if analysis.get("pytorch_detected"):
            candidates.append(
                self._candidate(
                    category="framework",
                    candidate="PyTorch optimization review",
                    reason=(
                        "PyTorch workload detected. Review device "
                        "placement, execution mode, and available "
                        "backend optimizations."
                    ),
                    evidence=["pytorch_detected=True"],
                )
            )

        if analysis.get("cuda_references"):
            candidates.append(
                self._candidate(
                    category="device",
                    candidate="CUDA portability review",
                    reason=(
                        "CUDA-related references were detected. "
                        "Review whether the workload can use "
                        "AMD ROCm-compatible execution paths."
                    ),
                    evidence=["cuda_references=True"],
                )
            )

        if analysis.get("rocm_references") or analysis.get(
            "hip_references"
        ):
            candidates.append(
                self._candidate(
                    category="amd_runtime",
                    candidate="ROCm/HIP optimization review",
                    reason=(
                        "ROCm or HIP references were detected. "
                        "Review AMD-specific runtime configuration "
                        "and execution behavior."
                    ),
                    evidence=[
                        f"rocm_references="
                        f"{analysis.get('rocm_references')}",
                        f"hip_references="
                        f"{analysis.get('hip_references')}",
                    ],
                )
            )

        tensor_operations = analysis.get("tensor_operations", [])

        if tensor_operations:
            candidates.append(
                self._candidate(
                    category="tensor_operations",
                    candidate="Tensor operation review",
                    reason=(
                        f"{len(tensor_operations)} tensor-related "
                        "operation types were detected. Review "
                        "operation efficiency and memory behavior."
                    ),
                    evidence=[
                        f"tensor_operations={tensor_operations}"
                    ],
                )
            )

        model_operations = analysis.get("model_operations", [])

        if model_operations:
            candidates.append(
                self._candidate(
                    category="model",
                    candidate="Model execution review",
                    reason=(
                        f"{len(model_operations)} model-related "
                        "operation types were detected. Review "
                        "inference/training execution efficiency."
                    ),
                    evidence=[
                        f"model_operations={model_operations}"
                    ],
                )
            )

        if analysis.get("gpu_usage_detected"):
            candidates.append(
                self._candidate(
                    category="gpu",
                    candidate="GPU execution review",
                    reason=(
                        "GPU-related code was detected. Benchmark "
                        "GPU execution and investigate device "
                        "utilization and memory behavior."
                    ),
                    evidence=["gpu_usage_detected=True"],
                )
            )

        return candidates

    @staticmethod
    def _candidate(
        category: str,
        candidate: str,
        reason: str,
        evidence: list[str],
    ) -> dict:
        """Create a structured optimization candidate."""

        return {
            "category": category,
            "candidate": candidate,
            "reason": reason,
            "evidence": evidence,
            "status": "candidate",
            "requires_human_approval": True,
            "verification_required": True,
        }
