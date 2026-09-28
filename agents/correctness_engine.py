
import math
from numbers import Real


class CorrectnessEngine:
    """
    Compare reference and candidate outputs.

    Supports:
    - Integers and floating-point numbers
    - Strings, booleans, bytes and None
    - Lists and tuples
    - Dictionaries

    Floating-point values are compared using configurable
    relative and absolute tolerances.
    """

    def __init__(
        self,
        rel_tol: float = 1e-5,
        abs_tol: float = 1e-8,
    ):
        if rel_tol < 0 or abs_tol < 0:
            raise ValueError("Tolerances must be non-negative.")

        self.rel_tol = rel_tol
        self.abs_tol = abs_tol

    def compare(self, reference, candidate) -> dict:
        mismatches = []

        def check(expected, actual, path="output"):
            # Booleans must be checked before numbers because
            # bool is a subclass of int in Python.
            if isinstance(expected, bool) or isinstance(actual, bool):
                if type(expected) is not type(actual) or expected != actual:
                    mismatches.append({
                        "path": path,
                        "expected": repr(expected),
                        "actual": repr(actual),
                        "reason": "Boolean values differ.",
                    })
                return

            # Compare numeric values with tolerance.
            if isinstance(expected, Real) and isinstance(actual, Real):
                if not math.isclose(
                    expected,
                    actual,
                    rel_tol=self.rel_tol,
                    abs_tol=self.abs_tol,
                ):
                    mismatches.append({
                        "path": path,
                        "expected": repr(expected),
                        "actual": repr(actual),
                        "reason": "Numeric values exceed tolerance.",
                    })
                return

            # Require matching types for non-numeric values.
            if type(expected) is not type(actual):
                mismatches.append({
                    "path": path,
                    "expected": repr(expected),
                    "actual": repr(actual),
                    "reason": "Types differ.",
                })
                return

            if isinstance(expected, dict):
                expected_keys = set(expected)
                actual_keys = set(actual)

                for key in sorted(
                    expected_keys - actual_keys,
                    key=repr,
                ):
                    mismatches.append({
                        "path": f"{path}[{key!r}]",
                        "expected": repr(expected[key]),
                        "actual": "<missing>",
                        "reason": "Key missing from candidate.",
                    })

                for key in sorted(
                    actual_keys - expected_keys,
                    key=repr,
                ):
                    mismatches.append({
                        "path": f"{path}[{key!r}]",
                        "expected": "<missing>",
                        "actual": repr(actual[key]),
                        "reason": "Unexpected key in candidate.",
                    })

                for key in sorted(
                    expected_keys & actual_keys,
                    key=repr,
                ):
                    check(
                        expected[key],
                        actual[key],
                        f"{path}[{key!r}]",
                    )
                return

            if isinstance(expected, (list, tuple)):
                if len(expected) != len(actual):
                    mismatches.append({
                        "path": path,
                        "expected": f"length {len(expected)}",
                        "actual": f"length {len(actual)}",
                        "reason": "Sequence lengths differ.",
                    })

                for index, (left, right) in enumerate(
                    zip(expected, actual)
                ):
                    check(left, right, f"{path}[{index}]")
                return

            if isinstance(expected, (str, bytes, type(None))):
                if expected != actual:
                    mismatches.append({
                        "path": path,
                        "expected": repr(expected),
                        "actual": repr(actual),
                        "reason": "Values differ.",
                    })
                return

            raise TypeError(
                f"Unsupported output type at {path}: "
                f"{type(expected).__name__}"
            )

        check(reference, candidate)

        return {
            "passed": len(mismatches) == 0,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "rel_tol": self.rel_tol,
            "abs_tol": self.abs_tol,
        }
