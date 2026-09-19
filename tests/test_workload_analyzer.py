from agents.workload_analyzer import WorkloadAnalyzer


def main():
    analyzer = WorkloadAnalyzer("workloads/sample_workload.py")
    result = analyzer.analyze()

    print("=" * 60)
    print("AMD AI WORKLOAD DOCTOR")
    print("WORKLOAD ANALYSIS")
    print("=" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("=" * 60)


if __name__ == "__main__":
    main()
