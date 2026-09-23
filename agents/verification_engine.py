class VerificationEngine:
    """
    Verify whether an optimization produced an acceptable result.

    The verifier does not execute workloads.
    It evaluates supplied evidence.
    """

    def verify(
        self,
        before_benchmark: dict,
        after_benchmark: dict,
        correctness_result: dict,
    ) -> dict:
        """Return a structured verification result."""

        before_time = before_benchmark.get(
            "average_time_seconds"
        )
        after_time = after_benchmark.get(
            "average_time_seconds"
        )

        if before_time is None or after_time is None:
            raise ValueError(
                "Both benchmark results must contain "
                "average_time_seconds."
            )

        correctness_passed = (
            correctness_result.get("passed", False)
        )

        improvement_percent = 0.0

        if before_time > 0:
            improvement_percent = (
                (before_time - after_time)
                / before_time
            ) * 100

        performance_improved = after_time < before_time

        if correctness_passed and performance_improved:
            decision = "accept"

        elif not correctness_passed:
            decision = "reject"

        else:
            decision = "reject"

        return {
            "correctness_passed": correctness_passed,
            "performance_improved": performance_improved,
            "improvement_percent": improvement_percent,
            "decision": decision,
            "verified": correctness_passed
            and performance_improved,
        }
