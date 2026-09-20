from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
}


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


def validate_repository(repo_path: str) -> Path:

    repo = Path(repo_path).resolve()

    if not repo.exists():
        raise ValueError(
            f"Repository does not exist: {repo}"
        )

    if not repo.is_dir():
        raise ValueError(
            f"Path is not a directory: {repo}"
        )

    return repo


def discover_files(repo_path: str):

    repo = validate_repository(repo_path)

    files = []

    for file_path in repo.rglob("*"):

        if not file_path.is_file():
            continue

        # Ignore generated/vendor directories
        if any(
            part in IGNORED_DIRECTORIES
            for part in file_path.parts
        ):
            continue

        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        files.append(
            str(file_path.relative_to(repo))
        )

    return files