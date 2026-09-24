import posixpath
import re
from collections import Counter


def normalize_category(value):
    category = str(value or "").strip().lower()
    if any(term in category for term in ("security", "injection", "secret", "vulnerability", "unsafe code")):
        return "security"
    if any(word in category for word in ("optimization", "performance", "database")):
        return "optimization"
    return re.sub(r"[^a-z0-9]+", "_", category).strip("_")


def normalize_file(value):
    return posixpath.normpath(str(value or "").replace("\\", "/")).removeprefix("./")


def infer_finding_type(finding):
    explicit = finding.get("type")
    if explicit:
        return re.sub(r"[^a-z0-9]+", "_", str(explicit).lower()).strip("_")

    text = " ".join(
        str(finding.get(key, ""))
        for key in ("category", "title", "description", "evidence", "recommendation")
    ).lower()
    if re.search(r"\beval\b", text):
        return "unsafe_eval"
    if any(term in text for term in ("command injection", "os.system", "shell command")):
        return "command_injection"
    if any(term in text for term in ("sql injection", "sql query", "query construction", "sql is dynamically")):
        return "sql_injection"
    if any(term in text for term in ("hardcoded", "hard-coded", "api key", "secret", "credential")):
        return "hardcoded_secret"
    return re.sub(
        r"[^a-z0-9]+", "_", str(finding.get("title", "unknown")).lower()
    ).strip("_")


def finding_key(finding):
    return (
        normalize_category(finding.get("category")),
        infer_finding_type(finding),
        normalize_file(finding.get("file")),
    )


def calculate_detection_metrics(expected_findings, actual_findings):
    expected_keys = [finding_key(item) for item in expected_findings]
    actual_keys = [finding_key(item) for item in actual_findings]
    expected_counts = Counter(expected_keys)
    actual_counts = Counter(actual_keys)
    true_positives = sum(
        min(count, actual_counts[key])
        for key, count in expected_counts.items()
    )
    false_positives = len(actual_keys) - true_positives
    false_negatives = len(expected_keys) - true_positives

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    unmatched_expected = expected_counts.copy()
    for key in actual_keys:
        if unmatched_expected[key] > 0:
            unmatched_expected[key] -= 1
    missed_findings = []
    for finding, key in zip(expected_findings, expected_keys):
        if unmatched_expected[key] > 0:
            missed_findings.append(finding)
            unmatched_expected[key] -= 1

    unmatched_expected_for_actual = expected_counts.copy()
    false_positive_findings = []
    for finding, key in zip(actual_findings, actual_keys):
        if unmatched_expected_for_actual[key] > 0:
            unmatched_expected_for_actual[key] -= 1
        else:
            false_positive_findings.append(finding)

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "missed_findings": missed_findings,
        "false_positive_findings": false_positive_findings,
    }


def jaccard_similarity(findings_a, findings_b):
    keys_a = {finding_key(item) for item in findings_a}
    keys_b = {finding_key(item) for item in findings_b}
    union = keys_a | keys_b
    if not union:
        return 1.0
    return len(keys_a & keys_b) / len(union)


def calculate_consistency(runs):
    comparisons = []
    for left_index in range(len(runs)):
        for right_index in range(left_index + 1, len(runs)):
            left = runs[left_index]
            right = runs[right_index]
            comparisons.append({
                "run_a": left["run_id"],
                "run_b": right["run_id"],
                "jaccard_similarity": jaccard_similarity(
                    left.get("findings", []), right.get("findings", [])
                ),
            })
    average = (
        sum(item["jaccard_similarity"] for item in comparisons) / len(comparisons)
        if comparisons
        else 1.0
    )
    return {"pairwise_jaccard": comparisons, "average_consistency": average}


def calculate_performance(runs):
    def values(name):
        return [float(run.get(name) or 0) for run in runs]

    def average(items):
        return sum(items) / len(items) if items else 0.0

    latencies = values("latency")
    return {
        "average_latency": average(latencies),
        "min_latency": min(latencies) if latencies else 0.0,
        "max_latency": max(latencies) if latencies else 0.0,
        "average_total_tokens": average(values("total_tokens")),
        "average_tool_calls": average(values("tool_calls")),
    }
