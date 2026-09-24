import re

from .knowledge import load_knowledge


def _terms(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _document_terms(document: dict) -> set[str]:
    searchable = [document.get("title", "")]
    for field in ("keywords", "cwe", "owasp", "description", "indicators"):
        searchable.extend(document.get(field, []))
    return _terms(" ".join(str(value) for value in searchable))


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Return the highest-scoring local guidance entries for a query."""
    query_terms = _terms(query)
    if not query_terms or top_k <= 0:
        return []

    normalized_query = " ".join(query.lower().split())
    scored = []
    for position, document in enumerate(load_knowledge()):
        title = str(document.get("title", ""))
        terms = _document_terms(document)
        overlap = query_terms & terms
        if not overlap:
            continue

        score = len(overlap)
        if normalized_query in title.lower():
            score += len(query_terms) + 2
        if score < 2:
            continue
        scored.append((score, -position, document))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [document for _, _, document in scored[:top_k]]
