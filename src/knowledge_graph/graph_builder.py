"""Knowledge Graph Builder.

Builds a flat JSON Knowledge Graph of Evidence nodes for the Data
Classification (DC) domain, from data already present in the project:

1. data/maturity_models/DC_MQ_*.json - the authoritative source for each
   MQ's domain, levels, and per-Evidence maturity_requirement /
   related_specifications / inherits_previous_level_requirements.
2. data/evidence_catalog/DC_MQ_*_evidence.json - the acceptance_criteria for
   each Evidence Code.
3. data/knowledge_catalog/dc_knowledge_catalog.json - used only as a
   sanity cross-check that every Evidence in the flattened catalog was
   picked up while walking the maturity models.
4. knowledge_base/knowledge_sources.json - the registered knowledge sources,
   whose declared "used_for" tags determine which sources are recorded as
   an Evidence node's source_documents.
5. reports/reference_engine_report.txt - the Reference Engine's own report,
   parsed back into structured per-Evidence reference entries (document
   name, source type, page number, matching method, confidence, page role,
   matched text) that populate each node's references field.

No AI, RAG, embeddings, LLM, or graph database is used, and no PDF is opened
directly - the reference details come from re-parsing the Reference
Engine's already-generated text report. This produces a plain, static JSON
document; no relationships beyond a node's own fields are created, and
edges between nodes are deliberately out of scope for this phase.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.reference_engine.reference_engine import REPORT_PATH
from src.reference_engine.reference_validator import parse_evidence_blocks

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MATURITY_MODELS_DIR = PROJECT_ROOT / "data" / "maturity_models"
EVIDENCE_CATALOG_DIR = PROJECT_ROOT / "data" / "evidence_catalog"
KNOWLEDGE_CATALOG_PATH = (
    PROJECT_ROOT / "data" / "knowledge_catalog" / "dc_knowledge_catalog.json"
)
KNOWLEDGE_SOURCES_PATH = PROJECT_ROOT / "knowledge_base" / "knowledge_sources.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "knowledge_graph" / "dc_knowledge_graph.json"

# The Evidence-node fields that are populated straight from the maturity
# models / evidence catalogs. A registered knowledge source is recorded as a
# node's source_document only if its declared "used_for" tags overlap this
# set - i.e. it is documented as the origin of at least one of these fields.
POPULATED_FIELD_NAMES = {
    "description",
    "maturity_requirement",
    "acceptance_criteria",
    "inherits_previous_level_requirements",
}


def load_maturity_models() -> list[dict[str, Any]]:
    """Read every MQ's maturity model file (data/maturity_models/DC_MQ_*.json)."""
    models = []
    for path in sorted(MATURITY_MODELS_DIR.glob("DC_MQ_*.json")):
        with path.open("r", encoding="utf-8") as file:
            models.append(json.load(file))
    return models


def load_acceptance_criteria_by_code() -> dict[str, list[str]]:
    """Read every MQ's evidence catalog file and index acceptance_criteria by code."""
    acceptance_by_code: dict[str, list[str]] = {}
    for path in sorted(EVIDENCE_CATALOG_DIR.glob("DC_MQ_*_evidence.json")):
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        for item in data.get("evidence_items", []):
            acceptance_by_code[item["code"]] = item.get("acceptance_criteria", [])
    return acceptance_by_code


def load_knowledge_catalog_codes() -> set[str]:
    """Read the flattened Knowledge Catalog and return its set of Evidence codes.

    Used only as a cross-check count, not as a data source for the nodes
    themselves.
    """
    with KNOWLEDGE_CATALOG_PATH.open("r", encoding="utf-8") as file:
        catalog = json.load(file)
    return {entry["evidence_code"] for entry in catalog}


def load_knowledge_sources() -> list[dict[str, Any]]:
    """Read the registry of knowledge sources (knowledge_base/knowledge_sources.json)."""
    with KNOWLEDGE_SOURCES_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data["knowledge_sources"]


def compute_source_documents(sources: list[dict[str, Any]]) -> list[str]:
    """Return the registered source names that declare they build any populated field."""
    return [
        source["source_name"]
        for source in sources
        if set(source.get("used_for", [])) & POPULATED_FIELD_NAMES
    ]


def load_references_by_evidence_code() -> dict[str, list[dict[str, Any]]]:
    """Re-parse the Reference Engine's report into per-Evidence reference entries.

    Reuses the report parser already written for the Reference Validator
    (src/reference_engine/reference_validator.py) rather than re-implementing
    it, so there is a single place that understands the report's layout.
    """
    if not REPORT_PATH.exists():
        return {}

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    body_end = report_text.find("أدلة بدون أي مرجع")
    excluded_start = report_text.find("مطابقات مستبعدة")
    end_index = body_end if body_end != -1 else excluded_start
    body_text = report_text[: end_index if end_index != -1 else len(report_text)]

    references_by_code: dict[str, list[dict[str, Any]]] = {}
    for evidence in parse_evidence_blocks(body_text):
        references_by_code[evidence.evidence_code] = [
            {
                "document_name": match.document_name,
                "source_type": match.source_type_in_report,
                "page_number": match.page_number,
                "matched_by": match.matched_by,
                "confidence": match.confidence,
                "page_role": match.page_role,
                "matched_text": match.matched_text,
            }
            for match in evidence.matches
        ]
    return references_by_code


def dedupe_references(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop duplicate references, keeping only the first occurrence.

    Two references are considered duplicates when document_name, page_number,
    page_role, and source_type all match.
    """
    seen: set[tuple[Any, Any, Any, Any]] = set()
    deduped: list[dict[str, Any]] = []
    for reference in references:
        key = (
            reference.get("document_name"),
            reference.get("page_number"),
            reference.get("page_role"),
            reference.get("source_type"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(reference)
    return deduped


def build_nodes(
    maturity_models: list[dict[str, Any]],
    acceptance_by_code: dict[str, list[str]],
    source_documents: list[str],
    references_by_code: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Turn every Evidence entry across every maturity model into one graph node."""
    nodes: list[dict[str, Any]] = []
    for model in maturity_models:
        mq_id = model["mq_id"]
        domain_code = model["domain_code"]
        domain_name_ar = model["domain_name_ar"]

        for level in model.get("levels", []):
            level_number = level["level_number"]
            level_name = level["level_name"]
            level_description = level.get("description")

            for evidence in level.get("evidence", []):
                evidence_code = evidence["evidence_code"]
                nodes.append(
                    {
                        "evidence_code": evidence_code,
                        "evidence_name": evidence["evidence_name"],
                        "mq_id": mq_id,
                        "domain": {"code": domain_code, "name_ar": domain_name_ar},
                        "level": {"number": level_number, "name": level_name},
                        "description": level_description,
                        "maturity_requirement": evidence.get("maturity_requirement"),
                        "acceptance_criteria": acceptance_by_code.get(evidence_code, []),
                        "inherits_previous_level_requirements": evidence.get(
                            "inherits_previous_level_requirements", False
                        ),
                        "references": dedupe_references(references_by_code.get(evidence_code, [])),
                        "source_documents": source_documents,
                    }
                )

    nodes.sort(key=lambda node: (node["mq_id"], node["level"]["number"], node["evidence_code"]))
    return nodes


def build_graph(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap the node list in a small, self-describing graph document."""
    domain = nodes[0]["domain"] if nodes else {}
    return {
        "graph_id": "DC_KNOWLEDGE_GRAPH",
        "domain": domain,
        "version": "1.0",
        "node_count": len(nodes),
        "nodes": nodes,
    }


def run() -> None:
    """Entry point: load inputs, build the graph, and save it to disk."""
    maturity_models = load_maturity_models()
    acceptance_by_code = load_acceptance_criteria_by_code()
    sources = load_knowledge_sources()
    source_documents = compute_source_documents(sources)
    references_by_code = load_references_by_evidence_code()

    nodes = build_nodes(maturity_models, acceptance_by_code, source_documents, references_by_code)

    catalog_codes = load_knowledge_catalog_codes()
    node_codes = {node["evidence_code"] for node in nodes}
    if catalog_codes != node_codes:
        missing = catalog_codes - node_codes
        extra = node_codes - catalog_codes
        print(
            "تحذير: عدم تطابق بين Knowledge Catalog والعقد المبنية - "
            f"مفقودة: {sorted(missing)} | زائدة: {sorted(extra)}"
        )

    graph = build_graph(nodes)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(graph, file, ensure_ascii=False, indent=2)

    nodes_with_references = sum(1 for node in nodes if node["references"])

    print(f"عدد العقد (Nodes) التي تم إنشاؤها: {len(nodes)}")
    print(f"عدد العقد التي لديها references: {nodes_with_references}")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    run()
