from agents.verification_engine import VerificationEngine


def main():
    verifier = VerificationEngine()

    before = {
        "average_time_seconds": 1.20,
    }

    after = {
        "average_time_seconds": 0.90,
    }

    correctness = {
        "passed": False,
    }

    result = verifier.verify(
        before_benchmark=before,
        after_benchmark=after,
        correctness_result=correctness,
    )

    print("=" * 60)
    print("AMD AI WORKLOAD DOCTOR")
    print("VERIFICATION REJECTION TEST")
    print("=" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("=" * 60)

    if result["decision"] != "reject":
        raise AssertionError(
            "Verification should reject failed correctness."
        )

    print("rejection_test: PASSED")


if __name__ == "__main__":
    main()
