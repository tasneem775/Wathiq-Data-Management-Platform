"""Supporting Evidence File Service.

Connects the DOCX Evidence Reader to the Supporting Evidence Detector:
reads a real Word evidence file for a given evidence_code, then hands the
extracted text/tables/images information to the detector to decide whether
supporting evidence is required and whether it was found.

No LLM, no OCR, no OpenAI/OpenRouter, no LangChain, no external API is
used here.
"""

from __future__ import annotations

import sys
from typing import Any

from src.evidence_assessment.docx_evidence_reader import read_docx_evidence
from src.evidence_assessment.supporting_evidence_detector import (
    check_detected_supporting_evidence,
    detect_supporting_evidence_requirements,
)


def assess_supporting_evidence_file(evidence_code: str, file_path: str) -> dict[str, Any]:
    """Read a Word evidence file and assess its supporting-evidence requirements.

    Args:
        evidence_code: The evidence code (e.g. "DC.C.1.1") this file belongs to.
        file_path: Path to the .docx evidence file to read.

    Returns:
        A unified result dict. If the file could not be read successfully,
        service_status = "file_read_failed" and requirement_result /
        supporting_evidence_result are None. Otherwise service_status =
        "success" and both results plus a summary are included.
    """
    document_result = read_docx_evidence(file_path)

    if document_result["read_status"] != "success":
        return {
            "evidence_code": evidence_code,
            "file_result": document_result,
            "requirement_result": None,
            "supporting_evidence_result": None,
            "service_status": "file_read_failed",
            "warnings": document_result["warnings"],
        }

    requirement_result = detect_supporting_evidence_requirements(evidence_code)

    supporting_evidence_result = check_detected_supporting_evidence(
        evidence_code,
        {
            "text": document_result["text"],
            "images_count": document_result["images_count"],
            "tables_count": document_result["tables_count"],
            "paragraphs_count": document_result["paragraphs_count"],
            "file_name": document_result["file_name"],
        },
    )

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

    summary = {
        "supporting_evidence_required": supporting_evidence_result["supporting_evidence_required"],
        "supporting_evidence_status": supporting_evidence_result["supporting_evidence_status"],
        "required_supporting_types_count": len(supporting_evidence_result["required_supporting_types"]),
        "detected_supporting_types_count": len(supporting_evidence_result["detected_supporting_types"]),
        "missing_supporting_types_count": len(supporting_evidence_result["missing_supporting_types"]),
        "needs_human_review": supporting_evidence_result["needs_human_review"],
    }

    return {
        "evidence_code": evidence_code,
        "service_status": "success",
        "file_result": file_result,
        "requirement_result": requirement_result,
        "supporting_evidence_result": supporting_evidence_result,
        "summary": summary,
        "warnings": document_result["warnings"],
    }


def assess_multiple_supporting_evidence_files(items: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Run assess_supporting_evidence_file for a batch of {evidence_code, file_path} items."""
    return [
        assess_supporting_evidence_file(item["evidence_code"], item["file_path"])
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
        python -m src.evidence_assessment.supporting_evidence_file_service "DC.C.1.1" "path/to/file.docx"
    """
    if len(sys.argv) < 3:
        _safe_print("ضع evidence_code ومسار ملف DOCX لاختبار الخدمة.")
        return

    evidence_code = sys.argv[1]
    file_path = sys.argv[2]

    result = assess_supporting_evidence_file(evidence_code, file_path)

    file_result = result["file_result"] or {}
    supporting_evidence_result = result["supporting_evidence_result"] or {}

    lines = [
        f"evidence_code: {result['evidence_code']}",
        f"service_status: {result['service_status']}",
        f"file_name: {file_result.get('file_name')}",
        f"paragraphs_count: {file_result.get('paragraphs_count')}",
        f"tables_count: {file_result.get('tables_count')}",
        f"images_count: {file_result.get('images_count')}",
        f"supporting_evidence_required: {supporting_evidence_result.get('supporting_evidence_required')}",
        f"required_supporting_types: {supporting_evidence_result.get('required_supporting_types')}",
        f"detected_supporting_types: {supporting_evidence_result.get('detected_supporting_types')}",
        f"supporting_evidence_status: {supporting_evidence_result.get('supporting_evidence_status')}",
        f"missing_supporting_types: {supporting_evidence_result.get('missing_supporting_types')}",
        f"needs_human_review: {supporting_evidence_result.get('needs_human_review')}",
        f"warnings: {result['warnings']}",
    ]
    for line in lines:
        _safe_print(line)


if __name__ == "__main__":
    main()
