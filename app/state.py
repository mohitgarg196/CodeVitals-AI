from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Set


@dataclass
class ToolExecution:
    tool_name: str
    arguments: dict
    allowed: bool
    result: Any = None
    error: Optional[str] = None


@dataclass
class Observation:
    tool: str
    file: Optional[str] = None
    line: Optional[int] = None
    summary: str = ""
    evidence: str = ""


class VerificationStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class VerificationResult:
    finding_id: str
    status: str
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    output: str = ""
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class AgentState:

    task: str
    repo_path: str

    iteration: int = 0
    tool_calls: int = 0

    files_inspected: Set[str] = field(
        default_factory=set
    )

    tool_history: List[ToolExecution] = field(
        default_factory=list
    )

    observations: List[Observation] = field(
        default_factory=list
    )

    blocked_actions: int = 0
    rag_queries: int = 0
    rag_results: int = 0
    verification_results: List[VerificationResult] = field(default_factory=list)
    verifications_requested: int = 0
    verifications_passed: int = 0
    verifications_failed: int = 0
    verifications_error: int = 0
    verifications_timeout: int = 0
