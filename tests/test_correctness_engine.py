
import unittest

from agents.correctness_engine import CorrectnessEngine


class TestCorrectnessEngine(unittest.TestCase):

    def setUp(self):
        self.engine = CorrectnessEngine()

    def test_identical_outputs_pass(self):
        reference = {
            "result": [1, 2, 3],
            "status": True,
        }

        candidate = {
            "result": [1, 2, 3],
            "status": True,
        }

        result = self.engine.compare(reference, candidate)

        self.assertTrue(result["passed"])
        self.assertEqual(result["mismatch_count"], 0)

    def test_floating_point_tolerance(self):
        reference = [1.0, 2.0, 3.0]
        candidate = [1.0000001, 2.0000001, 3.0000001]

        result = self.engine.compare(reference, candidate)

        self.assertTrue(result["passed"])

    def test_incorrect_output_is_rejected(self):
        reference = {
            "result": [10, 20, 30],
            "status": True,
        }

        candidate = {
            "result": [10, 25, 30],
            "status": True,
        }

        result = self.engine.compare(reference, candidate)

        self.assertFalse(result["passed"])
        self.assertEqual(result["mismatch_count"], 1)
        self.assertEqual(
            result["mismatches"][0]["path"],
            "output['result'][1]",
        )

    def test_missing_dictionary_key_is_rejected(self):
        reference = {"latency": 0.5, "status": "ok"}
        candidate = {"latency": 0.5}

        result = self.engine.compare(reference, candidate)

        self.assertFalse(result["passed"])

    def test_boolean_and_integer_are_not_equivalent(self):
        result = self.engine.compare(True, 1)

        self.assertFalse(result["passed"])

    def test_sequence_length_mismatch_is_rejected(self):
        result = self.engine.compare([1, 2, 3], [1, 2])

        self.assertFalse(result["passed"])

    def test_negative_tolerance_is_rejected(self):
        with self.assertRaises(ValueError):
            CorrectnessEngine(rel_tol=-1)


if __name__ == "__main__":
    unittest.main()
