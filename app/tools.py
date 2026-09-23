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


def list_files(repo_path: str) -> dict:
    """
    List source files available in the repository.
    """

    repo = Path(repo_path)

    files = []

    for file_path in repo.rglob("*"):

        if not file_path.is_file():
            continue

        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        files.append(str(file_path.relative_to(repo)))

    return {
        "files": files,
        "count": len(files),
    }


def read_file(repo_path: str, file_path: str) -> dict:
    """
    Read the contents of a specific source file.
    """

    repo = Path(repo_path)
    target = repo / file_path

    # Prevent paths such as ../../secret.txt
    try:
        target = target.resolve()
        repo = repo.resolve()

        target.relative_to(repo)

    except ValueError:
        return {
            "error": "Access denied: path is outside repository."
        }

    if not target.exists():
        return {
            "error": f"File not found: {file_path}"
        }

    if not target.is_file():
        return {
            "error": f"Not a file: {file_path}"
        }

    try:
        content = target.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except Exception as exc:
        return {
            "error": f"Unable to read file: {exc}"
        }

    return {
        "file": file_path,
        "content": content,
    }


def search_code(repo_path: str, query: str) -> dict:
    """
    Search for a text pattern across supported source files.
    """

    repo = Path(repo_path)

    matches = []

    for file_path in repo.rglob("*"):

        if not file_path.is_file():
            continue

        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            lines = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            ).splitlines()
        except Exception:
            continue

        for line_number, line in enumerate(lines, start=1):

            if query.lower() in line.lower():

                matches.append({
                    "file": str(file_path.relative_to(repo)),
                    "line": line_number,
                    "content": line.strip(),
                })

    return {
        "query": query,
        "matches": matches,
        "count": len(matches),
    }


def get_dependencies(repo_path: str) -> dict:
    """
    Inspect common dependency files in the repository.
    """

    repo = Path(repo_path)

    dependency_files = [
        "requirements.txt",
        "package.json",
        "pom.xml",
        "go.mod",
    ]

    dependencies = {}

    for filename in dependency_files:

        path = repo / filename

        if not path.exists():
            continue

        try:
            dependencies[filename] = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            continue

    return {
        "dependencies": dependencies
    }

def read_file_region(
    repo_path: str,
    file_path: str,
    start_line: int,
    end_line: int,
) -> dict:

    repo = Path(repo_path).resolve()
    target = (repo / file_path).resolve()

    try:
        target.relative_to(repo)
    except ValueError:
        return {
            "error": "Access denied: path is outside repository."
        }

    if not target.exists():
        return {
            "error": f"File not found: {file_path}"
        }

    if not target.is_file():
        return {
            "error": f"Not a file: {file_path}"
        }

    try:
        lines = target.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()

    except Exception as exc:
        return {
            "error": f"Unable to read file: {exc}"
        }

    # Keep line numbers within valid bounds.
    start_line = max(1, start_line)
    end_line = min(len(lines), end_line)

    selected_lines = []

    for line_number in range(start_line, end_line + 1):
        selected_lines.append(
            f"{line_number}: {lines[line_number - 1]}"
        )

    return {
        "file": file_path,
        "start_line": start_line,
        "end_line": end_line,
        "content": "\n".join(selected_lines),
        "total_file_lines": len(lines),
    }