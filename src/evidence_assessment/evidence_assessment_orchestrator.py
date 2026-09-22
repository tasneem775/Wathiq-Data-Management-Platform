"""Evidence Assessment Orchestrator.

Connects the DOCX Evidence Reader, the Gap Analysis Engine, and the
Supporting Evidence File Service into a single unified evidence-assessment
result for a real Word evidence file.

No LLM, no OCR, no OpenAI/OpenRouter, no LangChain, no external API is
used here.
"""

from __future__ import annotations

import sys
from typing import Any

from src.evidence_assessment.docx_evidence_reader import read_docx_evidence
from src.evidence_assessment.gap_analysis_engine import analyze_gap
from src.evidence_assessment.supporting_evidence_file_service import (
    assess_supporting_evidence_file,
)

_KNOWN_TEXT_STATUSES = {"PASS", "PARTIAL_PASS", "FAIL", "NOT_PROVIDED"}


def _compute_combined_overall_status(text_overall_status: str, supporting_evidence_status: str) -> str:
    """Combine the text-compliance status and the supporting-evidence status.

    Priority order: UNKNOWN, then FAIL, then PARTIAL_PASS, then PASS — an
    UNKNOWN input on either side must never resolve to PASS/PARTIAL_PASS.
    """
    if text_overall_status not in _KNOWN_TEXT_STATUSES or supporting_evidence_status == "UNKNOWN":
        return "UNKNOWN"

    if text_overall_status == "FAIL" or supporting_evidence_status == "MISSING":
        return "FAIL"

    if text_overall_status == "PARTIAL_PASS" or supporting_evidence_status == "PARTIAL":
        return "PARTIAL_PASS"

    if text_overall_status == "PASS" and supporting_evidence_status in {"SATISFIED", "NOT_REQUIRED"}:
        return "PASS"

    return "UNKNOWN"


def _build_combined_summary(
    evidence_code: str,
    document_result: dict[str, Any],
    text_compliance_result: dict[str, Any],
    supporting_service_result: dict[str, Any],
) -> dict[str, Any]:
    supporting_summary = supporting_service_result["summary"]

    combined_overall_status = _compute_combined_overall_status(
        text_compliance_result["overall_status"],
        supporting_summary["supporting_evidence_status"],
    )

    needs_human_review = bool(
        text_compliance_result["needs_human_review"] or supporting_summary["needs_human_review"]
    )

    return {
        "evidence_code": evidence_code,
        "file_name": document_result["file_name"],
        "text_overall_status": text_compliance_result["overall_status"],
        "text_coverage_percentage": text_compliance_result["coverage_percentage"],
        "mandatory_requirement_passed": text_compliance_result["mandatory_requirement_passed"],
        "critical_missing_count": len(text_compliance_result["critical_missing"]),
        "medium_missing_count": len(text_compliance_result["medium_missing"]),
        "supporting_evidence_required": supporting_summary["supporting_evidence_required"],
        "supporting_evidence_status": supporting_summary["supporting_evidence_status"],
        "required_supporting_types_count": supporting_summary["required_supporting_types_count"],
        "detected_supporting_types_count": supporting_summary["detected_supporting_types_count"],
        "missing_supporting_types_count": supporting_summary["missing_supporting_types_count"],
        "images_count": document_result["images_count"],
        "tables_count": document_result["tables_count"],
        "combined_overall_status": combined_overall_status,
        "needs_human_review": needs_human_review,
    }


def assess_evidence_document(evidence_code: str, file_path: str) -> dict[str, Any]:
    """Read a Word evidence file and produce a unified assessment result.

    Args:
        evidence_code: The evidence code (e.g. "DC.C.1.1") this file belongs to.
        file_path: Path to the .docx evidence file to read.

    Returns:
        A unified result dict combining the DOCX reader, the Gap Analysis
        Engine, and the Supporting Evidence File Service. If the file could
        not be read successfully, assessment_status = "file_read_failed"
        and text_compliance_result / supporting_evidence_result /
        combined_summary are None.
    """
    document_result = read_docx_evidence(file_path)

    if document_result["read_status"] != "success":
        return {
            "evidence_code": evidence_code,
            "assessment_status": "file_read_failed",
            "document_result": document_result,
            "text_compliance_result": None,
            "supporting_evidence_result": None,
            "combined_summary": None,
            "warnings": document_result["warnings"],
        }

    text_compliance_result = analyze_gap(evidence_code, document_result["text"])

    supporting_service_result = assess_supporting_evidence_file(evidence_code, file_path)

    file_result = {
        "file_name": document_result["file_name"],
        "read_status": document_result["read_status"],
        "text_length": document_result["text_length"],
        "paragraphs_count": document_result["paragraphs_count"],
        "tables_count": document_result["tables_count"],
        "table_rows_count": document_result["table_rows_count"],
        "images_count": document_result["images_count"],
        "image_files": document_result["image_files"],
        "warnings": document_result["warnings"],
    }

    combined_summary = _build_combined_summary(
        evidence_code, document_result, text_compliance_result, supporting_service_result
    )

    return {
        "evidence_code": evidence_code,
        "assessment_status": "success",
        "document_result": file_result,
        "text_compliance_result": text_compliance_result,
        "supporting_evidence_result": supporting_service_result,
        "combined_summary": combined_summary,
        "warnings": document_result["warnings"],
    }


def assess_multiple_evidence_documents(items: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Run assess_evidence_document for a batch of {evidence_code, file_path} items."""
    return [
        assess_evidence_document(item["evidence_code"], item["file_path"])
        for item in items
    ]


def _safe_print(line: str) -> None:
    try:
        print(line)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(line.encode(encoding, errors="replace").decode(encoding))


def main() -> None:
    """Command-line entry point.

    Usage:
        python -m src.evidence_assessment.evidence_assessment_orchestrator "DC.C.1.1" "evidence_repository/data_classification/MQ1/DC.C.1.1.docx"
    """
    if len(sys.argv) < 3:
        _safe_print("ضع evidence_code ومسار ملف DOCX لاختبار الـ Orchestrator.")
        return

    evidence_code = sys.argv[1]
    file_path = sys.argv[2]

    result = assess_evidence_document(evidence_code, file_path)

    document_result = result["document_result"] or {}
    combined_summary = result["combined_summary"] or {}

    lines = [
        f"evidence_code: {result['evidence_code']}",
        f"assessment_status: {result['assessment_status']}",
        f"file_name: {document_result.get('file_name')}",
        f"text_overall_status: {combined_summary.get('text_overall_status')}",
        f"text_coverage_percentage: {combined_summary.get('text_coverage_percentage')}",
        f"mandatory_requirement_passed: {combined_summary.get('mandatory_requirement_passed')}",
        f"critical_missing_count: {combined_summary.get('critical_missing_count')}",
        f"medium_missing_count: {combined_summary.get('medium_missing_count')}",
        f"supporting_evidence_required: {combined_summary.get('supporting_evidence_required')}",
        f"supporting_evidence_status: {combined_summary.get('supporting_evidence_status')}",
        f"required_supporting_types_count: {combined_summary.get('required_supporting_types_count')}",
        f"detected_supporting_types_count: {combined_summary.get('detected_supporting_types_count')}",
        f"missing_supporting_types_count: {combined_summary.get('missing_supporting_types_count')}",
        f"images_count: {combined_summary.get('images_count')}",
        f"tables_count: {combined_summary.get('tables_count')}",
        f"combined_overall_status: {combined_summary.get('combined_overall_status')}",
        f"needs_human_review: {combined_summary.get('needs_human_review')}",
        f"warnings: {result['warnings']}",
    ]
    for line in lines:
        _safe_print(line)


if __name__ == "__main__":
    main()
