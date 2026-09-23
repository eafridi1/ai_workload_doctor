from agents.governed_action import GovernedOptimizationAction


def main():
    action = GovernedOptimizationAction(
        action_id="OPT-0001",
        candidate="CUDA portability review",
        category="device",
        reason=(
            "CUDA-related references were detected. "
            "Review whether the workload can use "
            "AMD ROCm-compatible execution paths."
        ),
        evidence=[
            "cuda_references=True",
            "gpu_usage_detected=True",
        ],
    )

    print("=" * 60)
    print("AMD AI WORKLOAD DOCTOR")
    print("GOVERNED OPTIMIZATION ACTION")
    print("=" * 60)

    print(f"initial_status: {action.status}")

    action.recommend()
    print(f"after_recommendation: {action.status}")

    action.request_human_approval()
    print(f"approval_status: {action.status}")

    action.approve("human-reviewer")
    print(f"after_approval: {action.status}")
    print(f"human_approved: {action.human_approved}")

    action.mark_executed()
    print(f"after_execution: {action.status}")

    before = {
        "average_time_seconds": 1.20,
    }

    after = {
        "average_time_seconds": 0.90,
    }

    action.record_benchmark(
        before=before,
        after=after,
    )

    print(f"after_benchmark: {action.status}")

    verification = {
        "correctness_check": "passed",
        "output_match": True,
    }

    action.record_verification(verification)

    print(f"after_verification: {action.status}")

    action.accept()

    print(f"final_status: {action.status}")

    print("\n" + "=" * 60)
    print("GOVERNANCE HISTORY")
    print("=" * 60)

    for event in action.history:
        print(
            f"{event['status']}: "
            f"{event['details']}"
        )

    print("\n" + "=" * 60)
    print("SERIALIZED ACTION")
    print("=" * 60)

    result = action.to_dict()

    for key, value in result.items():
        print(f"{key}: {value}")

    print("=" * 60)


if __name__ == "__main__":
    main()
