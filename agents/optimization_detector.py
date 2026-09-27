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

        frameworks = analysis.get("frameworks", [])
        cuda_references = analysis.get("cuda_references", False)
        rocm_references = analysis.get("rocm_references", False)
        gpu_usage = analysis.get("gpu_usage", False)
        tensor_operations = analysis.get("tensor_operations", False)
        model_operations = analysis.get("model_operations", False)

        def add_candidate(
            category: str,
            candidate: str,
            reason: str,
            evidence: str,
        ):
            candidates.append(
                {
                    "category": category,
                    "candidate": candidate,
                    "reason": reason,
                    "evidence": evidence,
                    "status": "candidate",
                    "requires_human_approval": True,
                    "verification_required": True,
                }
            )

        if "PyTorch" in frameworks:
            add_candidate(
                category="framework_optimization",
                candidate="Review PyTorch execution for AMD/ROCm optimization opportunities.",
                reason=(
                    "The workload uses PyTorch and may benefit from "
                    "AMD-specific execution optimizations."
                ),
                evidence="PyTorch framework detected.",
            )

        if cuda_references:
            add_candidate(
                category="portability",
                candidate="Review CUDA-specific code for ROCm/HIP portability.",
                reason=(
                    "CUDA-related references were detected and should "
                    "be reviewed before AMD GPU execution."
                ),
                evidence="CUDA references detected in source code.",
            )

        if rocm_references:
            add_candidate(
                category="rocm_optimization",
                candidate="Review existing ROCm/HIP usage for optimization opportunities.",
                reason=(
                    "ROCm/HIP references were detected and may require "
                    "performance validation."
                ),
                evidence="ROCm/HIP references detected in source code.",
            )

        if tensor_operations:
            add_candidate(
                category="tensor_optimization",
                candidate="Review tensor operations for performance optimization.",
                reason=(
                    "Tensor-related operations were detected and should "
                    "be benchmarked for optimization opportunities."
                ),
                evidence="Tensor operations detected in workload.",
            )

        if model_operations:
            add_candidate(
                category="model_optimization",
                candidate="Review model execution for performance optimization.",
                reason=(
                    "Model-related operations were detected and should "
                    "be evaluated through benchmarking and verification."
                ),
                evidence="Model operations detected in workload.",
            )

        if gpu_usage:
            add_candidate(
                category="gpu_execution",
                candidate="Validate GPU execution and measure AMD GPU performance.",
                reason=(
                    "GPU-related source-code signals were detected. "
                    "Actual hardware execution must be benchmarked."
                ),
                evidence=(
                    "GPU-related source-code signal detected; "
                    "runtime GPU execution is not yet verified."
                ),
            )

        return candidates
