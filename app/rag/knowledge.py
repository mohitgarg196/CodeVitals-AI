import json
from pathlib import Path


KNOWLEDGE_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "knowledge" / "security"
)


def load_knowledge() -> list[dict]:
    """Load local security guidance JSON documents as dictionaries."""
    documents = []

    for path in sorted(KNOWLEDGE_DIRECTORY.glob("*.json")):
        with path.open(encoding="utf-8") as knowledge_file:
            documents.append(json.load(knowledge_file))

    return documents
