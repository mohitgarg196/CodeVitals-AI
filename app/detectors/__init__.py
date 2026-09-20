from .security import detect_security_patterns
from .optimization import detect_optimization_patterns


def detect_candidates(repo_path: str):
    candidates = []

    candidates.extend(
        detect_security_patterns(repo_path)
    )

    candidates.extend(
        detect_optimization_patterns(repo_path)
    )

    for index, candidate in enumerate(candidates, start=1):
        candidate["candidate_id"] = index

    return candidates