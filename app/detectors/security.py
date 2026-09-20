from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".go",
}


SECURITY_PATTERNS = {

    "os.system": {
        "title": "Potential Command Injection",
        "severity": "High",
        "description": (
            "os.system executes commands through a system shell "
            "and can be dangerous when influenced by untrusted input."
        ),
    },

    "eval(": {
        "title": "Potential Unsafe Code Execution",
        "severity": "High",
        "description": (
            "eval can execute arbitrary code and should not be "
            "used with untrusted input."
        ),
    },

    "exec(": {
        "title": "Potential Unsafe Code Execution",
        "severity": "High",
        "description": (
            "exec can execute arbitrary Python code."
        ),
    },

}


def detect_security_patterns(repo_path: str):

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

        relative_path = str(
            file_path.relative_to(repo)
        )

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            for pattern, metadata in SECURITY_PATTERNS.items():

                if pattern in line:

                    candidates.append({
                        "category": "security",
                        "detector": "pattern",
                        "pattern": pattern,
                        "severity": metadata["severity"],
                        "file": relative_path,
                        "line": line_number,
                        "title": metadata["title"],
                        "description": metadata["description"],
                        "evidence": line.strip(),
                    })

    return candidates