"""Assessment Results Store.

Persists one assessment_result dict (as produced by
evidence_assessment_orchestrator.assess_evidence_document) per evidence_code,
keyed under its domain, so that domain_progress_engine.calculate_domain_progress
can be run later against every evidence assessed so far — not just the ones
passed in-memory for a single call.

This is the accumulation layer that sits between "one evidence assessed" and
"all evidence assessed": every other component in the pipeline processes one
evidence file per call and returns its result to the caller without saving it
anywhere. This module is the only place that writes assessment results to
disk, and domain_progress_engine is the only intended reader.

No LLM, no OCR, no external API is used here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

RESULTS_DIR = Path("data/assessment_results")


def _result_file_path(domain_code: str) -> Path:
    return RESULTS_DIR / f"{domain_code}_results.json"


def save_assessment_result(domain_code: str, assessment_result: Dict[str, Any]) -> None:
    """يحفظ نتيجة تقييم دليل واحد ضمن ملف نتائج الدومين، مستبدلاً أي نتيجة سابقة لنفس الكود."""
    evidence_code = assessment_result.get("evidence_code")
    if not evidence_code:
        return

    file_path = _result_file_path(domain_code)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    results_by_code: Dict[str, Any] = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                results_by_code = json.load(f)
        except (json.JSONDecodeError, OSError):
            results_by_code = {}

    results_by_code[evidence_code] = assessment_result

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results_by_code, f, ensure_ascii=False, indent=2)


def load_assessment_results(domain_code: str) -> List[Dict[str, Any]]:
    """يقرأ كل نتائج التقييم المحفوظة لدومين معيّن كقائمة (شكل موحّد يقبله domain_progress_engine)."""
    file_path = _result_file_path(domain_code)
    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            results_by_code = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(results_by_code, dict):
        return []

    return list(results_by_code.values())
