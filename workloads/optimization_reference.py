
def sum_squares(n: int) -> int:
    """Calculate the sum of squares using a loop."""
    total = 0

    for number in range(1, n + 1):
        total += number * number

    return total


def run_workload():
    return sum_squares(500_000)


if __name__ == "__main__":
    print(run_workload())
