from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional


class Finding(BaseModel):
    category: str
    severity: str
    file: str
    line: Optional[int] = None
    title: str
    description: str
    recommendation: str


class AnalysisReport(BaseModel):
    findings: List[Finding]

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


def read_repository(repo_path: str) -> str:
    repo = Path(repo_path)

    files = []

    for file_path in repo.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            continue

        relative_path = file_path.relative_to(repo)

        files.append(
            f"""
===== FILE: {relative_path} =====

{content}
"""
        )

    return "\n".join(files)