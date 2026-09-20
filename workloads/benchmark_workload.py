def run_workload():
    total = 0

    for number in range(1, 1_000_001):
        total += number * number

    return total


if __name__ == "__main__":
    result = run_workload()
    print(result)
