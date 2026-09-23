from dataclasses import dataclass
from pathlib import Path

@dataclass
class BudgetManager:

    max_iterations: int = 10
    max_tool_calls: int = 32
    soft_tool_limit: int = 25

    iterations_used: int = 0
    tool_calls_used: int = 0

    def can_continue(self) -> bool:

        if self.iterations_used >= self.max_iterations:
            return False

        if self.tool_calls_used >= self.max_tool_calls:
            return False

        return True

    def record_iteration(self):

        self.iterations_used += 1

    def record_tool_call(self):

        self.tool_calls_used += 1

    def remaining_tool_calls(self):

        return (
            self.max_tool_calls
            - self.tool_calls_used
        )

    def should_wrap_up(self):
        return self.tool_calls_used >= self.soft_tool_limit

class PolicyEngine:

    ALLOWED_TOOLS = {
        "list_files",
        "read_file",
        "read_file_region",
        "search_code",
        "get_dependencies",
    }

    def is_tool_allowed(
        self,
        tool_name: str
    ) -> bool:

        return tool_name in self.ALLOWED_TOOLS

    def is_path_allowed(
        self,
        repo_path: str,
        file_path: str,
    ) -> bool:

        repo = Path(repo_path).resolve()

        target = (
            repo / file_path
        ).resolve()

        try:

            target.relative_to(repo)

            return True

        except ValueError:

            return False

class LoopDetector:

    def __init__(self):

        self.previous_actions = set()

    def is_duplicate(
        self,
        tool_name: str,
        arguments: dict
    ) -> bool:

        action = (
            tool_name,
            tuple(sorted(arguments.items()))
        )

        if action in self.previous_actions:
            return True

        self.previous_actions.add(action)

        return False

from .tools import (
    list_files,
    read_file,
    search_code,
    get_dependencies,
    read_file_region,
)


class ToolManager:

    AVAILABLE_TOOLS = {
        "list_files": list_files,
        "read_file": read_file,
        "search_code": search_code,
        "get_dependencies": get_dependencies,
        "read_file_region": read_file_region,
    }

    def __init__(
        self,
        policy: PolicyEngine,
        budget: BudgetManager,
        loop_detector: LoopDetector,
    ):

        self.policy = policy
        self.budget = budget
        self.loop_detector = loop_detector

    def execute(
        self,
        tool_name: str,
        arguments: dict,
    ):
        if tool_name in {"read_file", "read_file_region"}:
            repo_path = arguments.get("repo_path")
            file_path = arguments.get("file_path")

            if not self.policy.is_path_allowed(
                repo_path,
                file_path,
            ):
                return {
                    "status": "blocked",
                    "reason": "File path is outside the repository.",
                }

        # -----------------------------
        # 1. Permission check
        # -----------------------------

        if not self.policy.is_tool_allowed(tool_name):

            return {
                "status": "blocked",
                "reason": (
                    f"Tool '{tool_name}' "
                    "is not allowed."
                )
            }

        # -----------------------------
        # 2. Budget check
        # -----------------------------

        if not self.budget.can_continue():

            return {
                "status": "blocked",
                "reason": "Agent budget exceeded."
            }

        # -----------------------------
        # 3. Loop detection
        # -----------------------------

        if self.loop_detector.is_duplicate(
            tool_name,
            arguments
        ):

            return {
                "status": "blocked",
                "reason": (
                    "Duplicate tool call detected."
                )
            }

        # -----------------------------
        # 4. Execute
        # -----------------------------

        tool = self.AVAILABLE_TOOLS.get(
            tool_name
        )

        if tool is None:

            return {
                "status": "blocked",
                "reason": (
                    f"Unknown tool: {tool_name}"
                )
            }

        self.budget.record_tool_call()

        try:

            result = tool(**arguments)

            return {
                "status": "success",
                "result": result,
            }

        except Exception as exc:

            return {
                "status": "error",
                "reason": str(exc),
            }

class AgentHarness:

    def __init__(self):

        self.policy = PolicyEngine()

        self.budget = BudgetManager(
            max_iterations=10,
            max_tool_calls=32,
        )

        self.loop_detector = LoopDetector()

        self.tool_manager = ToolManager(
            policy=self.policy,
            budget=self.budget,
            loop_detector=self.loop_detector,
        )

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict,
    ):

        print(
            f"\n[HARNESS] Requested tool: "
            f"{tool_name}"
        )

        result = self.tool_manager.execute(
            tool_name,
            arguments,
        )

        print(
            f"[HARNESS] Status: "
            f"{result['status']}"
        )

        if result["status"] == "blocked":

            print(
                f"[HARNESS] Reason: "
                f"{result['reason']}"
            )

        return result

if __name__ == "__main__":

    harness = AgentHarness()

    print("\nTEST 1: Valid tool")

    print(
        harness.execute_tool(
            "list_files",
            {
                "repo_path": "test_repo"
            }
        )
    )

    print("\nTEST 2: Duplicate tool")

    print(
        harness.execute_tool(
            "list_files",
            {
                "repo_path": "test_repo"
            }
        )
    )

    print("\nTEST 3: Invalid tool")

    print(
        harness.execute_tool(
            "delete_repository",
            {
                "repo_path": "test_repo"
            }
        )
    )

    print("\nTEST 4: Path traversal")

    print(
        harness.execute_tool(
            "read_file",
            {
                "repo_path": "test_repo",
                "file_path": "../../.env",
            }
        )
    )
