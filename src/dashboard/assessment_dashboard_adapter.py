"""Dashboard Assessment Adapter.

Connects src/services/assessment_pipeline_service.py to the Dashboard UI
that will be built later. Takes an evidence_code and an uploaded DOCX file
path, runs the Assessment Pipeline, and turns the raw pipeline result into
a compact, safe-to-render Presentation Dict — without ever letting an
error from the pipeline crash the caller.

No LLM, no OCR, no OpenAI/OpenRouter, no LangChain, no Streamlit, no
external API is used here. This step does not build the UI itself.
"""

from __future__ import annotations

import sys
from typing import Any

from src.services.assessment_pipeline_service import run_assessment_pipeline

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

_STATUS_AR: dict[str, str] = {
    "PASS": "مستوفى",
    "PARTIAL_PASS": "مستوفى جزئياً",
    "FAIL": "غير مستوفى",
    "UNKNOWN": "غير معروف",
    "FILE_READ_FAILED": "تعذر قراءة الملف",
    "NOT_PROVIDED": "غير مقدم",
}


def _status_to_ar(status: str | None) -> str:
    return _STATUS_AR.get(status or "", "غير معروف")


def _map_pipeline_status_to_ui_status(pipeline_status: str | None) -> str:
    if pipeline_status == "success":
        return "success"
    if pipeline_status == "human_review_required":
        return "warning"
    if pipeline_status in ("file_read_failed", "assessment_failed"):
        return "error"
    return "error"


def _empty_word_report() -> dict[str, Any]:
    return {"generated": False, "path": None, "file_name": None, "size_bytes": None}


def _build_error_response(
    evidence_code: str,
    file_name: str | None,
    title: str,
    message: str,
    warnings: list[Any] | None,
) -> dict[str, Any]:
    return {
        "ui_status": "error",
        "title": title,
        "message": message,
        "evidence_code": evidence_code,
        "file_name": file_name,
        "assessment_available": False,
        "report_available": False,
        "summary_cards": [],
        "critical_findings": [],
        "medium_findings": [],
        "recommendations": {"high_priority": [], "medium_priority": []},
        "supporting_evidence": None,
        "word_report": None,
        "warnings": list(warnings) if warnings else [],
    }


def _extract_supporting_evidence(assessment_result: dict[str, Any]) -> dict[str, Any]:
    supporting_service_result = assessment_result.get("supporting_evidence_result") or {}
    detection = supporting_service_result.get("supporting_evidence_result") or {}
    return {
        "required": detection.get("supporting_evidence_required", False),
        "status": detection.get("supporting_evidence_status", "UNKNOWN"),
        "required_types": list(detection.get("required_supporting_types") or []),
        "detected_types": list(detection.get("detected_supporting_types") or []),
        "missing_types": list(detection.get("missing_supporting_types") or []),
        "needs_human_review": detection.get("needs_human_review", False),
    }


def _split_recommendations(recommendations: list[dict[str, Any]]) -> dict[str, Any]:
    high_priority = [r for r in recommendations if r.get("priority") == "HIGH"]
    medium_priority = [r for r in recommendations if r.get("priority") == "MEDIUM"]
    return {"high_priority": high_priority, "medium_priority": medium_priority}


def _extract_satisfied_findings(text_compliance_result: dict[str, Any]) -> list[str]:
    """Criterion texts gap_analysis_engine already marked PASS.

    text_compliance_result.criteria_results holds every critical/medium
    criterion with its PASS/FAIL status (src/evidence_assessment/
    gap_analysis_engine.py::analyze_gap). Only the FAIL ones were ever
    surfaced to the UI (as critical_missing/medium_missing) -- this adds
    the PASS side of the same already-computed list. No new computation.
    """
    criteria_results = text_compliance_result.get("criteria_results") or []
    return [item.get("criterion") for item in criteria_results if item.get("status") == "PASS"]


def _build_full_presentation(
    pipeline_result: dict[str, Any], ui_status: str, title: str, message: str
) -> dict[str, Any]:
    summary = pipeline_result.get("summary") or {}
    assessment_result = pipeline_result.get("assessment_result") or {}
    recommendation_result = pipeline_result.get("recommendation_result") or {}
    word_report = pipeline_result.get("word_report") or _empty_word_report()
    document_result = pipeline_result.get("document_result") or {}
    text_compliance_result = assessment_result.get("text_compliance_result") or {}

    overall_status = summary.get("combined_overall_status")
    overall_status_ar = _status_to_ar(overall_status)
    coverage_percentage = summary.get("text_coverage_percentage", 0)

    summary_cards = [
        {"key": "overall_status", "label": "الحالة العامة", "value": overall_status_ar},
        {"key": "coverage", "label": "نسبة التغطية", "value": f"{coverage_percentage}%"},
        {
            "key": "critical_missing",
            "label": "الفجوات الحرجة",
            "value": summary.get("critical_missing_count", 0),
        },
        {
            "key": "recommendations",
            "label": "إجمالي التوصيات",
            "value": summary.get("total_recommendations", 0),
        },
    ]

    document_metrics = {
        "paragraphs_count": document_result.get("paragraphs_count", 0),
        "tables_count": document_result.get("tables_count", 0),
        "images_count": document_result.get("images_count", 0),
        "text_length": document_result.get("text_length", 0),
    }

    text_assessment = {
        "status": text_compliance_result.get("overall_status"),
        "coverage_percentage": text_compliance_result.get("coverage_percentage", 0),
        "mandatory_requirement_passed": text_compliance_result.get(
            "mandatory_requirement_passed", False
        ),
        "passed_criteria": text_compliance_result.get("passed_criteria", 0),
        "failed_criteria": text_compliance_result.get("failed_criteria", 0),
    }

    return {
        "ui_status": ui_status,
        "title": title,
        "message": message,
        "evidence_code": summary.get("evidence_code") or pipeline_result.get("evidence_code"),
        "file_name": summary.get("file_name") or document_result.get("file_name"),
        "assessment_available": True,
        "report_available": bool(word_report.get("generated")),
        "overall_status": overall_status,
        "overall_status_ar": overall_status_ar,
        "coverage_percentage": coverage_percentage,
        "summary_cards": summary_cards,
        "document_metrics": document_metrics,
        "text_assessment": text_assessment,
        "supporting_evidence": _extract_supporting_evidence(assessment_result),
        "satisfied_findings": _extract_satisfied_findings(text_compliance_result),
        "critical_findings": list(text_compliance_result.get("critical_missing") or []),
        "medium_findings": list(text_compliance_result.get("medium_missing") or []),
        "recommendations": _split_recommendations(
            recommendation_result.get("recommendations") or []
        ),
        "word_report": word_report,
        "needs_human_review": summary.get("needs_human_review", False),
        "warnings": pipeline_result.get("warnings") or [],
    }


def prepare_dashboard_assessment(
    evidence_code: str, file_path: str, output_path: str | None = None
) -> dict[str, Any]:
    """Run the Assessment Pipeline for one evidence file and return a UI-safe Presentation Dict."""
    try:
        pipeline_result = run_assessment_pipeline(evidence_code, file_path, output_path=output_path)
    except Exception as error:  # noqa: BLE001 - never let the dashboard crash
        return _build_error_response(
            evidence_code=evidence_code,
            file_name=None,
            title="حدث خطأ غير متوقع",
            message="حدث خطأ غير متوقع أثناء تشغيل التقييم. يرجى المحاولة مرة أخرى.",
            warnings=[str(error)],
        )

    pipeline_status = pipeline_result.get("pipeline_status")
    document_result = pipeline_result.get("document_result") or {}

    if pipeline_status == "file_read_failed":
        return _build_error_response(
            evidence_code=evidence_code,
            file_name=document_result.get("file_name"),
            title="تعذر قراءة الملف",
            message="تعذر قراءة ملف الدليل المرفوع. يرجى التأكد من أن الملف بصيغة DOCX وصالح للقراءة.",
            warnings=pipeline_result.get("warnings"),
        )

    if pipeline_status == "assessment_failed":
        return _build_error_response(
            evidence_code=evidence_code,
            file_name=document_result.get("file_name"),
            title="فشل تقييم الدليل",
            message="تعذر إجراء تقييم آلي لهذا الدليل. يرجى المحاولة مرة أخرى أو مراجعته يدوياً.",
            warnings=pipeline_result.get("warnings"),
        )

    if pipeline_status == "human_review_required":
        return _build_full_presentation(
            pipeline_result,
            ui_status="warning",
            title="يتطلب مراجعة بشرية",
            message="تعذر اعتماد نتيجة تلقائية لهذا الدليل، ويجب مراجعته من مختص.",
        )

    if pipeline_status == "success":
        return _build_full_presentation(
            pipeline_result,
            ui_status="success",
            title="اكتمل تقييم الدليل",
            message="تم تحليل ملف الدليل وإنشاء نتيجة التقييم بنجاح.",
        )

    return _build_error_response(
        evidence_code=evidence_code,
        file_name=document_result.get("file_name"),
        title="حالة غير معروفة",
        message="تعذر تحديد نتيجة واضحة لتقييم هذا الدليل.",
        warnings=pipeline_result.get("warnings"),
    )


def prepare_multiple_dashboard_assessments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run prepare_dashboard_assessment for a batch of {evidence_code, file_path, output_path} items."""
    return [
        prepare_dashboard_assessment(
            item.get("evidence_code"), item.get("file_path"), item.get("output_path")
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
        python -m src.dashboard.assessment_dashboard_adapter "DC.C.1.1" "evidence_repository/data_classification/MQ1/DC.C.1.1.docx"
    """
    if len(sys.argv) < 3:
        _safe_print("ضع evidence_code ومسار ملف DOCX لاختبار Dashboard Assessment Adapter.")
        return

    evidence_code = sys.argv[1]
    file_path = sys.argv[2]

    presentation = prepare_dashboard_assessment(evidence_code, file_path)

    document_metrics = presentation.get("document_metrics") or {}
    supporting_evidence = presentation.get("supporting_evidence") or {}
    recommendations = presentation.get("recommendations") or {"high_priority": [], "medium_priority": []}
    word_report = presentation.get("word_report") or {}

    lines = [
        f"ui_status: {presentation.get('ui_status')}",
        f"title: {presentation.get('title')}",
        f"evidence_code: {presentation.get('evidence_code')}",
        f"file_name: {presentation.get('file_name')}",
        f"overall_status: {presentation.get('overall_status')}",
        f"overall_status_ar: {presentation.get('overall_status_ar')}",
        f"coverage_percentage: {presentation.get('coverage_percentage')}",
        f"summary_cards_count: {len(presentation.get('summary_cards') or [])}",
        f"paragraphs_count: {document_metrics.get('paragraphs_count')}",
        f"tables_count: {document_metrics.get('tables_count')}",
        f"images_count: {document_metrics.get('images_count')}",
        f"supporting_evidence_status: {supporting_evidence.get('status')}",
        f"critical_findings_count: {len(presentation.get('critical_findings') or [])}",
        f"medium_findings_count: {len(presentation.get('medium_findings') or [])}",
        f"high_priority_recommendations_count: {len(recommendations.get('high_priority') or [])}",
        f"medium_priority_recommendations_count: {len(recommendations.get('medium_priority') or [])}",
        f"report_available: {presentation.get('report_available')}",
        f"word_report_file_name: {word_report.get('file_name')}",
        f"needs_human_review: {presentation.get('needs_human_review')}",
        f"warnings: {presentation.get('warnings')}",
    ]
    for line in lines:
        _safe_print(line)


if __name__ == "__main__":
    main()
