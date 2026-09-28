
def sum_squares(n: int) -> int:
    """Calculate the sum of squares using a mathematical formula."""
    return n * (n + 1) * (2 * n + 1) // 6


def run_workload():
    return sum_squares(500_000)


if __name__ == "__main__":
    print(run_workload())
