import unittest

from evaluation.metrics import (
    calculate_detection_metrics,
    jaccard_similarity,
)


def finding(kind, file="src/example.py", title=None):
    return {
        "category": "security",
        "type": kind,
        "file": file,
        "title": title or kind,
    }


class DetectionMetricTests(unittest.TestCase):
    def test_perfect_detection(self):
        expected = [finding("issue_" + str(index)) for index in range(5)]
        result = calculate_detection_metrics(expected, list(expected))
        self.assertEqual(result["true_positives"], 5)
        self.assertEqual(result["false_positives"], 0)
        self.assertEqual(result["false_negatives"], 0)
        self.assertEqual(result["precision"], 1)
        self.assertEqual(result["recall"], 1)
        self.assertEqual(result["f1_score"], 1)

    def test_one_false_positive(self):
        expected = [finding("known")]
        actual = [finding("known"), finding("unexpected", "src/other.py")]
        result = calculate_detection_metrics(expected, actual)
        self.assertEqual((result["true_positives"], result["false_positives"]), (1, 1))
        self.assertEqual(result["precision"], 0.5)

    def test_one_false_negative(self):
        expected = [finding("known"), finding("missed", "src/other.py")]
        result = calculate_detection_metrics(expected, [finding("known")])
        self.assertEqual((result["true_positives"], result["false_negatives"]), (1, 1))
        self.assertEqual(result["recall"], 0.5)

    def test_zero_predicted_findings(self):
        result = calculate_detection_metrics([finding("known")], [])
        self.assertEqual(result["precision"], 0)
        self.assertEqual(result["recall"], 0)
        self.assertEqual(result["f1_score"], 0)
        self.assertEqual(len(result["missed_findings"]), 1)

    def test_zero_expected_findings(self):
        result = calculate_detection_metrics([], [finding("unexpected")])
        self.assertEqual(result["precision"], 0)
        self.assertEqual(result["recall"], 0)
        self.assertEqual(len(result["false_positive_findings"]), 1)


class ConsistencyMetricTests(unittest.TestCase):
    def test_identical_runs_have_jaccard_one(self):
        self.assertEqual(jaccard_similarity([finding("known")], [finding("known")]), 1)

    def test_completely_different_runs_have_jaccard_zero(self):
        self.assertEqual(jaccard_similarity([finding("one")], [finding("two")]), 0)

    def test_partially_overlapping_runs(self):
        left = [finding("one"), finding("two")]
        right = [finding("two"), finding("three")]
        self.assertEqual(jaccard_similarity(left, right), 1 / 3)


if __name__ == "__main__":
    unittest.main()
