import json
from pathlib import Path

from ..state import Observation


MAX_EVIDENCE_CHARS = 1500
MAX_RECENT_OBSERVATIONS = 5


class ContextManager:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def build_repository_index(self, files: list[str]) -> list[dict]:
        index = []

        for file_path in files:
            path = self.repo_path / file_path

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                index.append({
                    "file": file_path,
                    "extension": path.suffix,
                    "lines": len(content.splitlines()),
                    "characters": len(content),
                })
            except Exception:
                continue

        return index

    def rank_files(self, files, candidates):
        scores = {file_path: 0 for file_path in files}

        for candidate in candidates:
            candidate_file = candidate.get("file")
            if candidate_file in scores:
                scores[candidate_file] += 10

        return sorted(scores, key=lambda file_path: scores[file_path], reverse=True)

    def select_files(self, files, candidates, max_files=5):
        return self.rank_files(files, candidates)[:max_files]

    def _truncate_evidence(self, evidence: str) -> str:
        if not evidence:
            return ""
        if len(evidence) <= MAX_EVIDENCE_CHARS:
            return evidence
        return evidence[:MAX_EVIDENCE_CHARS] + "\n...[truncated]"

    def create_observation(self, tool_name, arguments, result):
        if tool_name == "search_code":
            matches = result.get("matches", [])
            if matches:
                match = matches[0]
                return Observation(
                    tool=tool_name,
                    file=match.get("file"),
                    line=match.get("line"),
                    summary=(
                        f"Search for '{result.get('query', '')}' "
                        f"returned {len(matches)} matches."
                    ),
                    evidence=self._truncate_evidence(match.get("content", "")),
                )
            return Observation(
                tool=tool_name,
                summary=f"Search for '{result.get('query', '')}' returned no matches.",
            )

        if tool_name == "read_file_region":
            return Observation(
                tool=tool_name,
                file=result.get("file"),
                line=result.get("start_line"),
                summary=(
                    f"Inspected source region {result.get('start_line')}-"
                    f"{result.get('end_line')}."
                ),
                evidence=self._truncate_evidence(result.get("content", "")),
            )

        if tool_name == "read_file":
            return Observation(
                tool=tool_name,
                file=result.get("file"),
                summary="Inspected repository file.",
                evidence=self._truncate_evidence(result.get("content", "")),
            )

        if tool_name == "list_files":
            return Observation(
                tool=tool_name,
                summary=f"Repository contains {result.get('count', 0)} supported files.",
            )

        if tool_name == "get_dependencies":
            dependencies = result.get("dependencies", {})
            return Observation(
                tool=tool_name,
                summary="Inspected dependency files: " + ", ".join(dependencies.keys()),
            )

        return Observation(tool=tool_name, summary=f"Executed {tool_name}.")

    def build_reasoning_context(self, state, candidates, relevant_files) -> dict:
        recent_observations = state.observations[-MAX_RECENT_OBSERVATIONS:]
        return {
            "repository": str(self.repo_path),
            "relevant_files": relevant_files,
            "files_inspected": sorted(state.files_inspected),
            "candidate_count": len(candidates),
            "recent_observations": [
                {
                    "tool": observation.tool,
                    "file": observation.file,
                    "line": observation.line,
                    "summary": observation.summary,
                    "evidence": observation.evidence,
                }
                for observation in recent_observations
            ],
        }

    def format_reasoning_context(self, state, candidates, relevant_files) -> str:
        context = self.build_reasoning_context(state, candidates, relevant_files)
        return json.dumps(context, indent=2, default=str)
