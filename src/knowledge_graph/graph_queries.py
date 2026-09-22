"""Knowledge Graph Query Layer.

A thin, dependency-free read layer over data/knowledge_graph/dc_knowledge_graph.json.
No AI, RAG, ChromaDB, LangChain, or any external index is used - every
function below is a plain filter over the JSON already produced by
src/knowledge_graph/graph_builder.py.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = PROJECT_ROOT / "data" / "knowledge_graph" / "dc_knowledge_graph.json"

DETAILED_REQUIREMENT_PAGE = "Detailed Requirement Page"
OFFICIAL_MATURITY_REFERENCE = "Official Maturity Reference"
SUPPORTING_POLICY_PAGE = "Supporting Policy Page"


@lru_cache(maxsize=1)
def _load_graph() -> dict[str, Any]:
    """Read and cache the Knowledge Graph JSON file."""
    with GRAPH_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _nodes() -> list[dict[str, Any]]:
    """Return every node in the graph."""
    return _load_graph().get("nodes", [])


def _references_by_role(evidence_code: str, page_role: str) -> list[dict[str, Any]]:
    """Return the references of one Evidence filtered to a single page_role."""
    return [
        reference
        for reference in get_references_by_code(evidence_code)
        if reference.get("page_role") == page_role
    ]


def get_evidence_by_code(evidence_code: str) -> dict[str, Any] | None:
    """Return the full Node for one Evidence Code, or None if not found."""
    for node in _nodes():
        if node.get("evidence_code") == evidence_code:
            return node
    return None


def get_references_by_code(evidence_code: str) -> list[dict[str, Any]]:
    """Return every reference recorded for one Evidence Code."""
    node = get_evidence_by_code(evidence_code)
    if node is None:
        return []
    return list(node.get("references", []))


def get_detailed_pages_by_code(evidence_code: str) -> list[dict[str, Any]]:
    """Return only the references classified as Detailed Requirement Page."""
    return _references_by_role(evidence_code, DETAILED_REQUIREMENT_PAGE)


def get_official_references_by_code(evidence_code: str) -> list[dict[str, Any]]:
    """Return only the references classified as Official Maturity Reference."""
    return _references_by_role(evidence_code, OFFICIAL_MATURITY_REFERENCE)


def get_supporting_policy_pages_by_code(evidence_code: str) -> list[dict[str, Any]]:
    """Return only the references classified as Supporting Policy Page."""
    return _references_by_role(evidence_code, SUPPORTING_POLICY_PAGE)


def get_evidence_by_mq(mq_id: str) -> list[dict[str, Any]]:
    """Return every Evidence Node belonging to one MQ."""
    return [node for node in _nodes() if node.get("mq_id") == mq_id]


def get_evidence_by_level(level_number: int) -> list[dict[str, Any]]:
    """Return every Evidence Node at one maturity level."""
    return [
        node
        for node in _nodes()
        if isinstance(node.get("level"), dict) and node["level"].get("number") == level_number
    ]


def get_acceptance_criteria_by_code(evidence_code: str) -> list[str]:
    """Return only the acceptance_criteria list for one Evidence Code."""
    node = get_evidence_by_code(evidence_code)
    if node is None:
        return []
    return list(node.get("acceptance_criteria", []))


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def run() -> None:
    """Demo run: exercise every query function against DC.M.6 and friends."""
    print("=" * 50)
    print("1) DC.M.6 كامل")
    print("=" * 50)
    _print_json(get_evidence_by_code("DC.M.6"))

    print()
    print("=" * 50)
    print("2) Detailed pages لـ DC.M.6")
    print("=" * 50)
    _print_json(get_detailed_pages_by_code("DC.M.6"))

    print()
    print("=" * 50)
    print("3) Official references لـ DC.M.6")
    print("=" * 50)
    _print_json(get_official_references_by_code("DC.M.6"))

    print()
    print("=" * 50)
    print("4) Supporting policy pages لـ DC.M.6")
    print("=" * 50)
    _print_json(get_supporting_policy_pages_by_code("DC.M.6"))

    print()
    print("=" * 50)
    print("5) عدد أدلة DC.MQ.2")
    print("=" * 50)
    print(len(get_evidence_by_mq("DC.MQ.2")))

    print()
    print("=" * 50)
    print("6) عدد أدلة Level 3")
    print("=" * 50)
    print(len(get_evidence_by_level(3)))


if __name__ == "__main__":
    run()
