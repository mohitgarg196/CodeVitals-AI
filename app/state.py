from dataclasses import dataclass, field
from typing import Any, List, Optional, Set


@dataclass
class ToolExecution:
    tool_name: str
    arguments: dict
    allowed: bool
    result: Any = None
    error: Optional[str] = None


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

    observations: list[Any] = field(
        default_factory=list
    )

    blocked_actions: int = 0