from core.doctor_pipeline import WorkloadDoctorPipeline


def main():
    analysis_workload = "workloads/sample_workload.py"
    benchmark_workload = "workloads/benchmark_workload.py"

    pipeline = WorkloadDoctorPipeline(
        workload_path=analysis_workload,
        benchmark_workload_path=benchmark_workload,
    )

    print("=" * 60)
    print("AMD AI WORKLOAD DOCTOR - STEP 8 INTEGRATION TEST")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. ANALYZE
    # ---------------------------------------------------------
    print("\n[1] ANALYSIS")

    analysis = pipeline.analyze()

    print(f"workload: {analysis['workload']}")
    print(f"language: {analysis['language']}")
    print(f"lines_of_code: {analysis['lines_of_code']}")
    print(f"frameworks: {analysis['frameworks']}")
    print(f"GPU usage detected: {analysis['gpu_usage']}")
    print(f"CUDA references: {analysis['cuda_references']}")
    print(f"ROCm references: {analysis['rocm_references']}")

    # ---------------------------------------------------------
    # 2. DETECT OPTIMIZATION CANDIDATES
    # ---------------------------------------------------------
    print("\n[2] OPTIMIZATION CANDIDATES")

    candidates = pipeline.detect_candidates(analysis)

    print(f"candidate_count: {len(candidates)}")

    if not candidates:
        raise AssertionError(
            "Expected optimization candidates from sample_workload.py."
        )

    for index, candidate in enumerate(candidates, start=1):
        print(f"\nCandidate {index}")
        print(f"category: {candidate['category']}")
        print(f"candidate: {candidate['candidate']}")
        print(f"reason: {candidate['reason']}")
        print(f"status: {candidate['status']}")
        print(
            f"human approval required: "
            f"{candidate['requires_human_approval']}"
        )
        print(
            f"verification required: "
            f"{candidate['verification_required']}"
        )

    # ---------------------------------------------------------
    # 3. GOVERNANCE
    # ---------------------------------------------------------
    print("\n[3] GOVERNANCE")

    selected_candidate = candidates[0]

    action = pipeline.create_action(
        candidate=selected_candidate,
        action_id="AMD-02-STEP-8-ACTION-001",
    )

    print(f"action_id: {action.action_id}")
    print(f"initial_status: {action.status}")

    action.recommend()
    print(f"after_recommendation: {action.status}")

    action.request_human_approval()
    print(f"after_human_gate: {action.status}")

    action.approve("human_reviewer")
    print(f"after_approval: {action.status}")

    # ---------------------------------------------------------
    # 4. BENCHMARK
    # ---------------------------------------------------------
    print("\n[4] BENCHMARK")

    before_benchmark = pipeline.benchmark()

    print(f"workload: {before_benchmark['workload']}")
    print(
        f"average time: "
        f"{before_benchmark['average_time_seconds']:.6f} seconds"
    )
    print(
        f"minimum time: "
        f"{before_benchmark['minimum_time_seconds']:.6f} seconds"
    )
    print(
        f"maximum time: "
        f"{before_benchmark['maximum_time_seconds']:.6f} seconds"
    )

    # No actual optimization is performed in this local integration test.
    # The same benchmark result is used as the "after" result.
    #
    # Therefore, the verifier should correctly reject the proposed
    # optimization because there is no measured improvement.
    after_benchmark = before_benchmark.copy()

    # ---------------------------------------------------------
    # 5. GOVERNED EXECUTION
    # ---------------------------------------------------------
    print("\n[5] GOVERNED EXECUTION")

    action.mark_executed()

    print(f"execution_status: {action.status}")

    # ---------------------------------------------------------
    # 6. VERIFICATION
    # ---------------------------------------------------------
    print("\n[6] VERIFICATION")

    verification = pipeline.verify(
        before=before_benchmark,
        after=after_benchmark,
        correctness_passed=True,
    )

    print(
        f"correctness_passed: "
        f"{verification['correctness_passed']}"
    )

    print(
        f"performance_improved: "
        f"{verification['performance_improved']}"
    )

    print(
        f"improvement_percent: "
        f"{verification['improvement_percent']:.2f}%"
    )

    print(f"decision: {verification['decision']}")
    print(f"verified: {verification['verified']}")

    action.record_benchmark(
        
            before_benchmark,
            after_benchmark,
        
    )

    action.record_verification(verification)

    # ---------------------------------------------------------
    # 7. ROLLBACK
    # ---------------------------------------------------------
    print("\n[7] ROLLBACK")

    if verification["decision"] != "accept":
        action.rollback(
            "Verification rejected the optimization because "
            "no performance improvement was measured."
        )

    print(f"final_status: {action.status}")

    # ---------------------------------------------------------
    # 8. ASSERTIONS
    # ---------------------------------------------------------
    assert len(candidates) > 0
    assert action.status == "rolled_back"
    assert verification["decision"] == "reject"
    assert verification["verified"] is False
    assert verification["performance_improved"] is False

    # ---------------------------------------------------------
    # 9. FINAL SUMMARY
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 8 INTEGRATION TEST PASSED")
    print("=" * 60)

    print("Analysis: PASS")
    print("Candidate detection: PASS")
    print("Human governance: PASS")
    print("Benchmarking: PASS")
    print("Verification: PASS")
    print("Rollback: PASS")

    print("\nImportant:")
    print(
        "This test validates the local pipeline mechanics only."
    )
    print(
        "It does NOT claim an AI performance improvement."
    )
    print(
        "AMD GPU/ROCm benchmarking will be performed later."
    )


if __name__ == "__main__":
    main()
