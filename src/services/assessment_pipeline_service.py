"""Assessment Pipeline Service.

Runs the full compliance-assessment pipeline for a single Evidence Code's
Word file: reads the document, runs the unified assessment (text
compliance + supporting evidence), generates recommendations, and produces
the final Word report. This will later be the main entry point used by
the Dashboard.

No LLM, no OCR, no OpenAI/OpenRouter, no LangChain, no external API is
used here.
"""

from __future__ import annotations

import sys
from typing import Any

from src.evidence_assessment.docx_evidence_reader import read_docx_evidence
from src.evidence_assessment.evidence_assessment_orchestrator import (
    assess_evidence_document,
)
from src.recommendations.compliance_recommendation_engine import (
    generate_recommendations,
)
from src.reports.word_report_generator import generate_word_report
from src.scoring.assessment_results_store import save_assessment_result


def _strip_document_result(document_result: dict[str, Any]) -> dict[str, Any]:
    """Drops the full extracted text so the pipeline result stays lightweight."""
    return {
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


def _empty_word_report() -> dict[str, Any]:
    return {
        "generated": False,
        "path": None,
        "file_name": None,
        "size_bytes": None,
    }


def _build_summary(
    evidence_code: str,
    document_result: dict[str, Any],
    combined_summary: dict[str, Any],
    recommendation_summary: dict[str, Any],
    word_report_generated: bool,
    word_report_path: str | None,
) -> dict[str, Any]:
    return {
        "evidence_code": evidence_code,
        "file_name": document_result["file_name"],
        "combined_overall_status": combined_summary["combined_overall_status"],
        "text_overall_status": combined_summary["text_overall_status"],
        "text_coverage_percentage": combined_summary["text_coverage_percentage"],
        "supporting_evidence_required": combined_summary["supporting_evidence_required"],
        "supporting_evidence_status": combined_summary["supporting_evidence_status"],
        "critical_missing_count": combined_summary["critical_missing_count"],
        "medium_missing_count": combined_summary["medium_missing_count"],
        "total_recommendations": recommendation_summary["total_recommendations"],
        "high_priority_count": recommendation_summary["high_priority_count"],
        "medium_priority_count": recommendation_summary["medium_priority_count"],
        "images_count": document_result["images_count"],
        "tables_count": document_result["tables_count"],
        "needs_human_review": combined_summary["needs_human_review"],
        "word_report_generated": word_report_generated,
        "word_report_path": word_report_path,
    }


def run_assessment_pipeline(
    evidence_code: str, file_path: str, output_path: str | None = None
) -> dict[str, Any]:
    """Run the full assessment pipeline for one Evidence Code's Word file.

    Args:
        evidence_code: The evidence code (e.g. "DC.C.1.1") this file belongs to.
        file_path: Path to the .docx evidence file to assess.
        output_path: Optional destination path for the generated Word report.

    Returns:
        A unified pipeline result dict. pipeline_status is one of:
        "file_read_failed", "assessment_failed", "human_review_required",
        or "success".
    """
    document_result = read_docx_evidence(file_path)

    if document_result["read_status"] != "success":
        return {
            "pipeline_status": "file_read_failed",
            "evidence_code": evidence_code,
            "file_path": file_path,
            "document_result": document_result,
            "assessment_result": None,
            "recommendation_result": None,
            "word_report": None,
            "summary": None,
            "warnings": document_result["warnings"],
        }

    assessment_result = assess_evidence_document(evidence_code, file_path)

    if assessment_result["assessment_status"] != "success":
        return {
            "pipeline_status": "assessment_failed",
            "evidence_code": evidence_code,
            "file_path": file_path,
            "document_result": _strip_document_result(document_result),
            "assessment_result": assessment_result,
            "recommendation_result": None,
            "word_report": None,
            "summary": None,
            "warnings": document_result["warnings"],
        }

    domain_code = evidence_code.split(".")[0]
    save_assessment_result(domain_code, assessment_result)

    combined_summary = assessment_result["combined_summary"]
    provided_evidence_text = document_result["text"]

    recommendation_result = generate_recommendations(evidence_code, provided_evidence_text)

    if combined_summary["combined_overall_status"] == "UNKNOWN":
        pipeline_status = "human_review_required"
        word_report = _empty_word_report()
    else:
        pipeline_status = "success"
        word_report_path = generate_word_report(
            evidence_code, provided_evidence_text, output_path=output_path
        )
        word_report = {
            "generated": True,
            "path": str(word_report_path),
            "file_name": word_report_path.name,
            "size_bytes": word_report_path.stat().st_size,
        }

    summary = _build_summary(
        evidence_code,
        document_result,
        combined_summary,
        recommendation_result["summary"],
        word_report["generated"],
        word_report["path"],
    )

    return {
        "pipeline_status": pipeline_status,
        "evidence_code": evidence_code,
        "file_path": file_path,
        "document_result": _strip_document_result(document_result),
        "assessment_result": assessment_result,
        "recommendation_result": recommendation_result,
        "word_report": word_report,
        "summary": summary,
        "warnings": document_result["warnings"],
    }


def run_multiple_assessment_pipelines(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run run_assessment_pipeline for a batch of {evidence_code, file_path, output_path} items."""
    return [
        run_assessment_pipeline(
            item["evidence_code"], item["file_path"], item.get("output_path")
        )
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
        python -m src.services.assessment_pipeline_service "DC.C.1.1" "evidence_repository/data_classification/MQ1/DC.C.1.1.docx"
    """
    if len(sys.argv) < 3:
        _safe_print("ضع evidence_code ومسار ملف DOCX لاختبار الـ Assessment Pipeline.")
        return

    evidence_code = sys.argv[1]
    file_path = sys.argv[2]

    result = run_assessment_pipeline(evidence_code, file_path)

    document_result = result["document_result"] or {}
    summary = result["summary"] or {}

    lines = [
        f"pipeline_status: {result['pipeline_status']}",
        f"evidence_code: {result['evidence_code']}",
        f"file_name: {document_result.get('file_name')}",
        f"combined_overall_status: {summary.get('combined_overall_status')}",
        f"text_coverage_percentage: {summary.get('text_coverage_percentage')}",
        f"supporting_evidence_status: {summary.get('supporting_evidence_status')}",
        f"total_recommendations: {summary.get('total_recommendations')}",
        f"images_count: {summary.get('images_count')}",
        f"tables_count: {summary.get('tables_count')}",
        f"needs_human_review: {summary.get('needs_human_review')}",
        f"word_report_generated: {summary.get('word_report_generated')}",
        f"word_report_path: {summary.get('word_report_path')}",
        f"warnings: {result['warnings']}",
    ]
    for line in lines:
        _safe_print(line)


if __name__ == "__main__":
    main()
