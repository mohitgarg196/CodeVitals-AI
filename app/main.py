import time

from .llm import analyze_with_agent


def main():

    repo_path = "test_repo"

    print("===================================")
    print("        SECUREOPT V1")
    print("       TOOL-USING AGENT")
    print("===================================\n")

    start_time = time.perf_counter()

    report, response, tool_calls = analyze_with_agent(
        repo_path
    )

    end_time = time.perf_counter()

    print("\n========== SECUREOPT REPORT ==========\n")

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

    print("\n========== V1 METRICS ==========")

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

    if response.usage_metadata:

        print(
            f"Input tokens          : "
            f"{response.usage_metadata.prompt_token_count}"
        )

        print(
            f"Output tokens         : "
            f"{response.usage_metadata.candidates_token_count}"
        )

        print(
            f"Total tokens          : "
            f"{response.usage_metadata.total_token_count}"
        )


if __name__ == "__main__":
    main()