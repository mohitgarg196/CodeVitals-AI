import contextlib
import io
import json
import re
import shutil
import tempfile
import time
from pathlib import Path

from app.analyzer import AnalysisReport
from app.llm import analyze_with_agent
from evaluation.metrics import (
    calculate_consistency,
    calculate_detection_metrics,
    calculate_performance,
    finding_key,
)
from evaluation.report import format_report


RUN_COUNT = 3
EVALUATION_DIR = Path(__file__).resolve().parent
BENCHMARK_DIR = EVALUATION_DIR / "benchmarks" / "security_basic"
RESULTS_PATH = EVALUATION_DIR / "results.json"


def _finding_dict(finding):
    if hasattr(finding, "model_dump"):
        return finding.model_dump()
    return finding.dict()


def _token_metric(log_text, metric_name, response_usage, response_key):
    matches = re.findall(
        rf"Cumulative {re.escape(metric_name)} tokens:\s*(\d+)", log_text
    )
    if matches:
        return int(matches[-1])
    return int(getattr(response_usage, response_key, 0) or 0)


def _analysis_copy(source, destination):
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("expected.json", "__pycache__", ".pytest_cache"),
    )


def _run_once(repo_path, run_number):
    captured = io.StringIO()
    started = time.perf_counter()
    response = None
    state = None
    error = None
    try:
        with contextlib.redirect_stdout(captured):
            response, state = analyze_with_agent(str(repo_path))
        report = AnalysisReport.model_validate_json(response.output_text)
        findings = [_finding_dict(finding) for finding in report.findings]
    except Exception as exc:
        findings = []
        error = f"{type(exc).__name__}: {exc}"
    latency = time.perf_counter() - started
    log_text = captured.getvalue()
    usage = getattr(response, "usage", None)
    input_tokens = _token_metric(log_text, "input", usage, "input_tokens")
    output_tokens = _token_metric(log_text, "output", usage, "output_tokens")
    total_tokens = _token_metric(log_text, "total", usage, "total_tokens")

    return {
        "run_id": f"run_{run_number}",
        "findings": findings,
        "finding_keys": [
            {"category": key[0], "type": key[1], "file": key[2]}
            for key in (finding_key(item) for item in findings)
        ],
        "latency": latency,
        "tool_calls": getattr(state, "tool_calls", 0),
        "iterations": getattr(state, "iteration", 0),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "files_inspected": len(getattr(state, "files_inspected", set())),
        "rag_queries": getattr(state, "rag_queries", 0),
        "rag_results": getattr(state, "rag_results", 0),
        "verifications_requested": getattr(state, "verifications_requested", 0),
        "verifications_passed": getattr(state, "verifications_passed", 0),
        "verifications_failed": getattr(state, "verifications_failed", 0),
        "error": error,
    }


def run_evaluation():
    configuration = json.loads(
        (BENCHMARK_DIR / "expected.json").read_text(encoding="utf-8")
    )
    expected_findings = configuration["findings"]
    runs = []

    # The expected labels stay outside the repository presented to the agent.
    with tempfile.TemporaryDirectory(prefix="codevitals-evaluation-") as temp_dir:
        analysis_repo = Path(temp_dir) / "security_basic"
        _analysis_copy(BENCHMARK_DIR, analysis_repo)
        for run_number in range(1, RUN_COUNT + 1):
            print(f"Running {configuration['benchmark']} ({run_number}/{RUN_COUNT})...")
            runs.append(_run_once(analysis_repo, run_number))

    all_expected = []
    all_actual = []
    for run in runs:
        all_expected.extend(expected_findings)
        all_actual.extend(run["findings"])
        run["detection_metrics"] = calculate_detection_metrics(
            expected_findings, run["findings"]
        )

    detection = calculate_detection_metrics(all_expected, all_actual)
    detection["expected_findings_per_run"] = len(expected_findings)
    detection["run_cases"] = RUN_COUNT
    detection["expected_run_cases"] = len(all_expected)

    false_positive_runs = [
        {"run_id": run["run_id"], "finding": finding}
        for run in runs
        for finding in run["detection_metrics"]["false_positive_findings"]
    ]
    missed_runs = [
        {"run_id": run["run_id"], "finding": finding}
        for run in runs
        for finding in run["detection_metrics"]["missed_findings"]
    ]
    detection["false_positive_findings"] = [item["finding"] for item in false_positive_runs]
    detection["false_positive_run_details"] = false_positive_runs
    detection["missed_findings"] = [item["finding"] for item in missed_runs]
    detection["missed_run_details"] = missed_runs

    results = {
        "benchmark": configuration["benchmark"],
        "runs": runs,
        "expected_finding_count": len(expected_findings),
        "detection_metrics": detection,
        "consistency_metrics": calculate_consistency(runs),
        "performance_metrics": calculate_performance(runs),
        "missed_findings": detection["missed_findings"],
        "false_positives": detection["false_positive_findings"],
    }
    RESULTS_PATH.write_text(
        json.dumps(results, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(format_report(results))
    print(f"Machine-readable results: {RESULTS_PATH}")
    return results


if __name__ == "__main__":
    run_evaluation()
