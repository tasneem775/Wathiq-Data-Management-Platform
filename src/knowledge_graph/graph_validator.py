"""Knowledge Graph Validator.

Reads data/knowledge_graph/dc_knowledge_graph.json and checks it for
structural completeness: the expected node count, every node carrying the
required fields, every node having at least one reference, every reference
carrying its required fields, DC.M.6's expected reference count, and that
DC.C.5.1 carries no left-over Open Data ("OD.5.1" / "سجل البيانات المفتوحة")
false positive.

No AI, RAG, embeddings, or PDF access - this is a plain, static check of the
JSON file already produced by src/knowledge_graph/graph_builder.py.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = PROJECT_ROOT / "data" / "knowledge_graph" / "dc_knowledge_graph.json"
VALIDATION_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "knowledge_graph_validation_report.txt"
)

EXPECTED_NODE_COUNT = 23

REQUIRED_NODE_FIELDS = (
    "evidence_code",
    "evidence_name",
    "mq_id",
    "domain",
    "level",
    "maturity_requirement",
    "acceptance_criteria",
    "references",
)

REQUIRED_REFERENCE_FIELDS = (
    "document_name",
    "source_type",
    "page_number",
    "matched_by",
    "confidence",
    "page_role",
    "matched_text",
)

DC_M6_CODE = "DC.M.6"
DC_M6_EXPECTED_REFERENCE_COUNT = 6

DC_C5_1_CODE = "DC.C.5.1"
OPEN_DATA_FORBIDDEN_STRINGS = ("OD.5.1", "سجل البيانات المفتوحة")

SEPARATOR = "-" * 50


@dataclass
class CheckResult:
    """One pass/fail assertion made by the validator."""

    scope: str
    check_name: str
    passed: bool
    detail: str


def load_graph() -> dict[str, Any]:
    """Read the Knowledge Graph JSON file."""
    with GRAPH_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def check_node_count(checks: list[CheckResult], nodes: list[dict[str, Any]]) -> None:
    """Test 1: the graph must have exactly EXPECTED_NODE_COUNT nodes."""
    passed = len(nodes) == EXPECTED_NODE_COUNT
    checks.append(
        CheckResult(
            scope="عام",
            check_name=f"عدد Nodes = {EXPECTED_NODE_COUNT}",
            passed=passed,
            detail=f"العدد الفعلي: {len(nodes)}",
        )
    )


def check_required_node_fields(checks: list[CheckResult], node: dict[str, Any]) -> None:
    """Test 2: a node must carry every field in REQUIRED_NODE_FIELDS."""
    missing = [field for field in REQUIRED_NODE_FIELDS if field not in node]
    passed = not missing
    checks.append(
        CheckResult(
            scope=node.get("evidence_code", "?"),
            check_name="يحتوي جميع الحقول المطلوبة للـ Node",
            passed=passed,
            detail=f"حقول مفقودة: {missing}" if missing else "جميع الحقول موجودة",
        )
    )


def check_has_reference(checks: list[CheckResult], node: dict[str, Any]) -> None:
    """Test 3: a node must have at least one reference."""
    references = node.get("references", [])
    passed = isinstance(references, list) and len(references) >= 1
    checks.append(
        CheckResult(
            scope=node.get("evidence_code", "?"),
            check_name="لديه reference واحد على الأقل",
            passed=passed,
            detail=f"عدد المراجع: {len(references) if isinstance(references, list) else 'غير قائمة'}",
        )
    )


def check_reference_fields(checks: list[CheckResult], node: dict[str, Any]) -> None:
    """Test 4: every reference on a node must carry every REQUIRED_REFERENCE_FIELDS key."""
    evidence_code = node.get("evidence_code", "?")
    references = node.get("references", [])
    if not isinstance(references, list):
        return
    for index, reference in enumerate(references, start=1):
        missing = [field for field in REQUIRED_REFERENCE_FIELDS if field not in reference]
        passed = not missing
        checks.append(
            CheckResult(
                scope=evidence_code,
                check_name=f"reference رقم ({index}) يحتوي جميع الحقول المطلوبة",
                passed=passed,
                detail=f"حقول مفقودة: {missing}" if missing else "جميع الحقول موجودة",
            )
        )


def check_dc_m6_reference_count(checks: list[CheckResult], nodes_by_code: dict[str, dict[str, Any]]) -> None:
    """Test 5: DC.M.6 must have exactly DC_M6_EXPECTED_REFERENCE_COUNT references."""
    node = nodes_by_code.get(DC_M6_CODE)
    if node is None:
        checks.append(
            CheckResult(
                scope=DC_M6_CODE,
                check_name=f"لديه {DC_M6_EXPECTED_REFERENCE_COUNT} references بالضبط",
                passed=False,
                detail="لم يتم العثور على DC.M.6 داخل الرسم البياني",
            )
        )
        return

    references = node.get("references", [])
    actual_count = len(references) if isinstance(references, list) else -1
    passed = actual_count == DC_M6_EXPECTED_REFERENCE_COUNT
    checks.append(
        CheckResult(
            scope=DC_M6_CODE,
            check_name=f"لديه {DC_M6_EXPECTED_REFERENCE_COUNT} references بالضبط",
            passed=passed,
            detail=f"العدد الفعلي: {actual_count}",
        )
    )


def check_dc_c5_1_no_open_data_leak(
    checks: list[CheckResult], nodes_by_code: dict[str, dict[str, Any]]
) -> None:
    """Test 6: DC.C.5.1 must carry no OD.5.1 / "سجل البيانات المفتوحة" reference."""
    node = nodes_by_code.get(DC_C5_1_CODE)
    if node is None:
        checks.append(
            CheckResult(
                scope=DC_C5_1_CODE,
                check_name="لا يحتوي أي reference فيه OD.5.1 أو سجل البيانات المفتوحة",
                passed=False,
                detail="لم يتم العثور على DC.C.5.1 داخل الرسم البياني",
            )
        )
        return

    references = node.get("references", [])
    offending: list[dict[str, Any]] = []
    if isinstance(references, list):
        for reference in references:
            matched_text = str(reference.get("matched_text", ""))
            document_name = str(reference.get("document_name", ""))
            if any(
                forbidden in matched_text or forbidden in document_name
                for forbidden in OPEN_DATA_FORBIDDEN_STRINGS
            ):
                offending.append(reference)

    passed = not offending
    checks.append(
        CheckResult(
            scope=DC_C5_1_CODE,
            check_name="لا يحتوي أي reference فيه OD.5.1 أو سجل البيانات المفتوحة",
            passed=passed,
            detail=(
                "لا توجد مطابقات بيانات مفتوحة مسربة"
                if passed
                else f"مطابقات مسربة: {offending}"
            ),
        )
    )


def build_validation_report(checks: list[CheckResult]) -> str:
    """Render the Arabic validation report."""
    passed_checks = sum(1 for check in checks if check.passed)
    failed_checks = sum(1 for check in checks if not check.passed)
    overall = "PASS" if failed_checks == 0 else "FAIL"

    lines: list[str] = []
    lines.append("=" * 50)
    lines.append("تقرير التحقق من Knowledge Graph")
    lines.append("Knowledge Graph Validator Report")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"عدد الاختبارات الناجحة: {passed_checks}")
    lines.append("")
    lines.append(f"عدد الاختبارات الفاشلة: {failed_checks}")
    lines.append("")
    lines.append(f"النتيجة النهائية: {overall}")
    lines.append("")
    lines.append("=" * 50)
    lines.append("")

    current_scope: str | None = None
    for check in checks:
        if check.scope != current_scope:
            current_scope = check.scope
            lines.append(SEPARATOR)
            lines.append("رمز الدليل:" if current_scope != "عام" else "فحص عام:")
            lines.append(current_scope)
            lines.append(SEPARATOR)
            lines.append("")

        status = "PASS" if check.passed else "FAIL"
        lines.append(f"[{status}] {check.check_name}")
        lines.append(check.detail)
        lines.append("")

    return "\n".join(lines) + "\n"


def run() -> None:
    """Entry point: load the graph, run every check, and save the report."""
    graph = load_graph()
    nodes = graph.get("nodes", [])
    nodes_by_code = {node.get("evidence_code"): node for node in nodes}

    checks: list[CheckResult] = []

    check_node_count(checks, nodes)

    for node in nodes:
        check_required_node_fields(checks, node)
        check_has_reference(checks, node)
        check_reference_fields(checks, node)

    check_dc_m6_reference_count(checks, nodes_by_code)
    check_dc_c5_1_no_open_data_leak(checks, nodes_by_code)

    report = build_validation_report(checks)

    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_REPORT_PATH.write_text(report, encoding="utf-8")

    passed_checks = sum(1 for check in checks if check.passed)
    failed_checks = sum(1 for check in checks if not check.passed)
    overall = "PASS" if failed_checks == 0 else "FAIL"

    print(f"عدد الاختبارات الناجحة: {passed_checks}")
    print(f"عدد الاختبارات الفاشلة: {failed_checks}")
    print(f"النتيجة النهائية: {overall}")
    print(VALIDATION_REPORT_PATH)


if __name__ == "__main__":
    run()
