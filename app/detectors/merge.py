def normalize(value: str) -> str:
    return " ".join(value.lower().split())


def finding_key(finding):
    return (
        normalize(finding.file),
        finding.line,
        normalize(finding.category),
    )


def deduplicate_findings(findings):
    unique = []
    seen = set()
    duplicate_count = 0

    for finding in findings:
        key = finding_key(finding)

        if key in seen:
            duplicate_count += 1
            continue

        seen.add(key)
        unique.append(finding)

    return unique, duplicate_count