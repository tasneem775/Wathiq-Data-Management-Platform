"""Domain Progress Dashboard Adapter.

Connects src/scoring/domain_progress_engine.py to the Dashboard UI that will
be built later. Loads every assessment result saved so far for a domain
(via assessment_results_store), computes domain-level progress, and turns it
into a compact, safe-to-render Presentation Dict — without ever letting an
error from the engine crash the caller.

No LLM, no OCR, no OpenAI/OpenRouter, no LangChain, no Streamlit, no
external API is used here. This step does not build the UI itself.
"""

from __future__ import annotations

import sys
from typing import Any

from src.scoring.domain_progress_engine import calculate_domain_progress_from_store

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _build_error_response(domain_code: str, message: str) -> dict[str, Any]:
    return {
        "ui_status": "error",
        "domain_code": domain_code,
        "message": message,
        "summary_cards": [],
        "mq_cards": [],
        "warnings": [],
    }


def _build_summary_cards(progress: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "key": "domain_compliance",
            "label": "نسبة الامتثال العامة",
            "value": f"{progress['domain_compliance_percentage']}%",
        },
        {
            "key": "assessment_completion",
            "label": "نسبة اكتمال التقييم",
            "value": f"{progress['assessment_completion_percentage']}%",
        },
        {
            "key": "assessed_evidence",
            "label": "الأدلة المُقيَّمة",
            "value": f"{progress['assessed_evidence']}/{progress['total_evidence']}",
        },
        {
            "key": "needs_human_review",
            "label": "بحاجة لمراجعة بشرية",
            "value": progress["needs_human_review_count"],
        },
    ]


def _build_mq_cards(mq_progress: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "mq_id": mq["mq_id"],
            "status": mq["mq_status"],
            "status_ar": mq["mq_status_ar"],
            "compliance_percentage": mq["compliance_percentage"],
            "assessment_completion_percentage": mq["assessment_completion_percentage"],
            "assessed_evidence": mq["assessed_evidence"],
            "total_evidence": mq["total_evidence"],
        }
        for mq in mq_progress
    ]


def prepare_domain_dashboard(domain_code: str = "DC") -> dict[str, Any]:
    """يحسب تقدم الدومين من النتائج المحفوظة ويعيد Presentation Dict آمناً للعرض."""
    try:
        progress = calculate_domain_progress_from_store(domain_code)
    except Exception as error:  # noqa: BLE001 - never let the dashboard crash
        return _build_error_response(
            domain_code, f"حدث خطأ غير متوقع أثناء حساب تقدم الدومين: {error}"
        )

    return {
        "ui_status": "success",
        "domain_code": progress["domain_code"],
        "domain_name": progress["domain_name"],
        "message": "تم حساب تقدم الدومين بنجاح.",
        "summary_cards": _build_summary_cards(progress),
        "mq_cards": _build_mq_cards(progress["mq_progress"]),
        "warnings": progress["warnings"],
    }


def _safe_print(line: str) -> None:
    try:
        print(line)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(line.encode(encoding, errors="replace").decode(encoding))


def main() -> None:
    """Command-line entry point.

    Usage:
        python -m src.dashboard.domain_progress_dashboard_adapter DC
    """
    domain_code = sys.argv[1] if len(sys.argv) > 1 else "DC"

    presentation = prepare_domain_dashboard(domain_code)

    lines = [
        f"ui_status: {presentation.get('ui_status')}",
        f"domain_code: {presentation.get('domain_code')}",
        f"message: {presentation.get('message')}",
        f"summary_cards: {presentation.get('summary_cards')}",
        f"mq_cards_count: {len(presentation.get('mq_cards') or [])}",
        f"warnings: {presentation.get('warnings')}",
    ]
    for line in lines:
        _safe_print(line)


if __name__ == "__main__":
    main()
