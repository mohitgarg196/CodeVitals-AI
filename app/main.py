from importlib.metadata import files
import time
import sys

from app.detectors.merge import deduplicate_findings

from .analyzer import AnalysisReport
from .llm import analyze_with_agent
from .repository.loader import discover_files


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python -m app.main <repository_path>"
        )

        sys.exit(1)


    repo_path = sys.argv[1]

    files = discover_files(repo_path)

    print("===================================")
    print("        CODEVITALS V3")
    print("       AGENT + HARNESS")
    print("===================================\n")

    print("\n========== REPOSITORY ==========")

    print(f"Repository : {repo_path}")
    print(f"Files      : {len(files)}")

    for file in files[:20]:
        print(f"  {file}")

    if len(files) > 20:
        print(
            f"  ... and {len(files) - 20} more"
        )

    start_time = time.perf_counter()

    response, state = analyze_with_agent(
        repo_path
    )
    if not getattr(response, "output_text", ""):
        print("\n[HARNESS] No final report was produced.")
        print(f"Iterations            : {state.iteration}")
        print(f"Tool calls            : {state.tool_calls}")
        print(f"Blocked actions       : {state.blocked_actions}")
        print(f"Files inspected       : {len(state.files_inspected)}")
        print(f"Compact context chars : unavailable (see iteration logs)")
        print(f"Raw tool result chars : logged per tool call")
        return

    report = AnalysisReport.model_validate_json(
        response.output_text
    )
    tool_calls = state.tool_calls

    investigated = report.investigated_candidates

    confirmed_candidates = [
        c for c in investigated
        if c.status == "confirmed"
    ]

    rejected_candidates = [
        c for c in investigated
        if c.status == "rejected"
    ]

    final_findings, duplicate_count = deduplicate_findings(
        report.findings
    )

    end_time = time.perf_counter()

    print("\n========== CODEVITALS REPORT ==========\n")

    for index, finding in enumerate(
        report.findings,
        start=1
    ):

        print(f"Finding #{index}")
        print(f"Category      : {finding.category}")
        print(f"Severity      : {finding.severity}")
        print(f"File          : {finding.file}")
        print(f"Line          : {finding.line}")
        print(f"Title         : {finding.title}")
        print(
            f"Description   : "
            f"{finding.description}"
        )
        print(
            f"Recommendation: "
            f"{finding.recommendation}"
        )

        print("-" * 60)

    security_findings = [
        finding
        for finding in report.findings
        if "security" in finding.category.lower()
    ]

    optimization_findings = [
        finding
        for finding in report.findings
            if any(
            keyword in finding.category.lower()
                for keyword in [
                    "optimization",
                    "performance",
                    "database",
                ]
            )
    ]

    print("\n========== V7 METRICS ==========")

    print(
        f"Latency               : "
        f"{end_time - start_time:.2f}s"
    )

    print(
        f"Total findings        : "
        f"{len(report.findings)}"
    )

    print(
        f"Security findings     : "
        f"{len(security_findings)}"
    )

    print(
        f"Optimization findings : "
        f"{len(optimization_findings)}"
    )

    print(
        f"Tool calls            : "
        f"{tool_calls}"
    )

    print(f"Iterations            : {state.iteration}")
    print(f"Blocked actions       : {state.blocked_actions}")
    print(f"Files inspected       : {len(state.files_inspected)}")
    print(f"Compact context chars : logged per iteration")
    print(f"Raw tool result chars : logged per tool call")

    if response.usage:

        print(
            f"Final response input tokens : "
            f"{response.usage.input_tokens}"
        )

        print(
            f"Final response output tokens: "
            f"{response.usage.output_tokens}"
        )

        print(
            f"Final response total tokens : "
            f"{response.usage.total_tokens}"
        )


if __name__ == "__main__":
    main()
