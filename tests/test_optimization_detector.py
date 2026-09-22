from agents.agent_principles import (
    AGENT_PRINCIPLES,
    COLLABORATION_MODEL,
)
from agents.human_gate import HumanApprovalGate
from agents.optimization_detector import OptimizationDetector
from agents.workload_analyzer import WorkloadAnalyzer


def main():
    analyzer = WorkloadAnalyzer(
        "workloads/sample_workload.py"
    )

    analysis = analyzer.analyze()

    detector = OptimizationDetector()
    candidates = detector.detect(analysis)

    gate = HumanApprovalGate()

    print("=" * 60)
    print("AMD AI WORKLOAD DOCTOR")
    print("OPTIMIZATION CANDIDATES")
    print("=" * 60)

    for index, candidate in enumerate(candidates, start=1):
        print(f"\nCandidate {index}")
        print(f"category: {candidate['category']}")
        print(f"candidate: {candidate['candidate']}")
        print(f"reason: {candidate['reason']}")
        print(f"evidence: {candidate['evidence']}")
        print(
            "requires_human_approval: "
            f"{candidate['requires_human_approval']}"
        )
        print(
            "verification_required: "
            f"{candidate['verification_required']}"
        )

        approval = gate.request_approval(candidate)

        print(f"approval_status: {approval['status']}")

    print("\n" + "=" * 60)
    print("4D PRINCIPLES")
    print("=" * 60)

    for principle, description in AGENT_PRINCIPLES.items():
        print(f"{principle}: {description}")

    print("\n" + "=" * 60)
    print("HUMAN / AGENT COLLABORATION")
    print("=" * 60)

    for key, value in COLLABORATION_MODEL.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 60)
    print(f"total_candidates: {len(candidates)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
