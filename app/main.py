import time

from .analyzer import read_repository
from .llm import analyze_with_llm


def main():

    repo_path = "test_repo"

    print("===================================")
    print("        SECUREOPT V0")
    print("===================================\n")

    print("Reading repository...")

    start_time = time.perf_counter()

    repository = read_repository(repo_path)

    print("Repository loaded.")
    print(f"Repository characters: {len(repository):,}")

    print("\nSending repository to Gemini...")

    report, response = analyze_with_llm(repository)

    end_time = time.perf_counter()

    print("\n========== SECUREOPT REPORT ==========\n")

    for index, finding in enumerate(report.findings, start=1):

        print(f"Finding #{index}")
        print(f"Category      : {finding.category}")
        print(f"Severity      : {finding.severity}")
        print(f"File          : {finding.file}")
        print(f"Line          : {finding.line}")
        print(f"Title         : {finding.title}")
        print(f"Description   : {finding.description}")
        print(f"Recommendation: {finding.recommendation}")

        print("-" * 60)

    print("\n========== METRICS ==========")

    print(f"Latency        : {end_time - start_time:.2f}s")
    print(f"Findings       : {len(report.findings)}")

    if response.usage_metadata:
        print(
            f"Input tokens   : "
            f"{response.usage_metadata.prompt_token_count}"
        )

        print(
            f"Output tokens  : "
            f"{response.usage_metadata.candidates_token_count}"
        )

        print(
            f"Total tokens   : "
            f"{response.usage_metadata.total_token_count}"
        )


if __name__ == "__main__":
    main()