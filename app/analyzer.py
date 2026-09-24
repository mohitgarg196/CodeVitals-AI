from pathlib import Path
import hashlib
import json
from pydantic import BaseModel
from typing import List, Optional


class CandidateFinding(BaseModel):
    candidate_id: int
    category: str
    detector: str
    severity: str
    file: str
    line: Optional[int] = None
    title: str
    description: str
    evidence: str
    pattern: Optional[str] = None


class InvestigatedCandidate(BaseModel):
    candidate_id: int
    status: str  # confirmed / rejected
    reason: str


class Finding(BaseModel):
    finding_id: str
    category: str
    severity: str
    file: str
    line: Optional[int] = None
    title: str
    description: str
    evidence: str
    recommendation: str
    proposed_patch: Optional[str] = None
    verification_command: Optional[str] = None
    source: str = "agent"


def make_finding_id(category, file, line, title):
    identity = json.dumps(
        [category, file, line, title],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return "FND-" + digest


class AnalysisReport(BaseModel):
    findings: List[Finding]
    investigated_candidates: List[InvestigatedCandidate] = []


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
