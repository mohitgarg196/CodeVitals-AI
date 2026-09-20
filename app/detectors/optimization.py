from pathlib import Path


SUPPORTED_EXTENSIONS = {".py"}

DATABASE_PATTERNS = {
    "find_one(",
    "find(",
    "findMany(",
    "execute(",
    "query(",
}


def get_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def detect_optimization_patterns(repo_path: str):
    repo = Path(repo_path).resolve()
    candidates = []

    for file_path in repo.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            lines = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).splitlines()
        except Exception:
            continue

        relative_path = str(file_path.relative_to(repo))

        loop_indent = None
        loop_line = None

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            current_indent = get_indent(line)

            # Detect a for/while loop
            if stripped.startswith("for ") or stripped.startswith("while "):
                loop_indent = current_indent
                loop_line = line_number
                continue

            # Exit loop when indentation returns to
            # the same or lower level
            if loop_indent is not None and current_indent <= loop_indent:
                loop_indent = None
                loop_line = None

            # Check database operations inside loop
            if loop_indent is not None:
                for pattern in DATABASE_PATTERNS:
                    if pattern in stripped:
                        candidates.append({
                            "category": "optimization",
                            "detector": "pattern",
                            "pattern": pattern,
                            "severity": "Medium",
                            "file": relative_path,
                            "line": line_number,
                            "title": "Potential N+1 Database Query",
                            "description": (
                                "A database operation appears to execute "
                                "inside a loop, which may cause repeated "
                                "database round trips."
                            ),
                            "evidence": stripped,
                            "loop_line": loop_line,
                        })
                        break

    return candidates