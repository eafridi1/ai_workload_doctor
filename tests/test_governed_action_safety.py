from agents.governed_action import GovernedOptimizationAction


def main():
    action = GovernedOptimizationAction(
        action_id="OPT-SAFETY-0001",
        candidate="Test optimization",
        category="test",
        reason="Verify human approval enforcement.",
        evidence=["synthetic_test=True"],
    )

    print("=" * 60)
    print("AMD AI WORKLOAD DOCTOR")
    print("GOVERNANCE SAFETY TEST")
    print("=" * 60)

    print(f"initial_status: {action.status}")

    try:
        action.mark_executed()
    except PermissionError as error:
        print("execution_without_approval: BLOCKED")
        print(f"reason: {error}")
    else:
        print("ERROR: execution was not blocked.")

    print("=" * 60)


if __name__ == "__main__":
    main()
