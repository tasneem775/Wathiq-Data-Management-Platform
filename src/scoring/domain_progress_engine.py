"""
Domain Progress Engine
=======================

يحسب تقدم مجال الامتثال (مثال: DC - تصنيف البيانات) بالاعتماد على:

1. كتالوج الأدلة الفعلي في data/evidence_catalog/ (مصدر الحقيقة لعدد الأدلة وربطها بالـ MQs).
2. نتائج تقييم جاهزة يتم تمريرها من Evidence Assessment Orchestrator أو Dashboard Adapter.

هذا المحرك لا يشغّل ملفات Word، ولا يقرأ أدلة خام، ولا يعيد تقييمها.
لا يستخدم أي LLM أو OCR أو أي خدمة خارجية.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

EVIDENCE_CATALOG_DIR = Path("data/evidence_catalog")

DOMAIN_NAMES_AR = {
    "DC": "تصنيف البيانات",
}

STATUS_LABELS_AR = {
    "PASS": "مستوفى",
    "PARTIAL_PASS": "مستوفى جزئياً",
    "FAIL": "غير مستوفى",
    "UNKNOWN": "غير معروف",
    "NOT_ASSESSED": "لم يتم التقييم",
}

VALID_STATUSES = {"PASS", "PARTIAL_PASS", "FAIL", "UNKNOWN"}

# اسم قديم (Deprecated) — يُبقى بلا تغيير في القيمة فقط لضمان توافق خلفي مع
# مستهلكين خارج نطاق src/evidence_assessment/ و src/scoring/ (تحديداً
# src/dashboard/domain_progress_dashboard_adapter.py الذي يقرأ mq_status
# بهذه القيم الحرفية). لا يوجد هذا في أي مصدر SDAIA/NDMO — هذه مفردات
# داخلية اخترعها هذا الملف. المفردات الصحيحة الجديدة هي
# EVIDENCE_STATUS_LABELS_AR أدناه؛ استخدمها في أي كود جديد.
MQ_STATUS_LABELS_AR = {
    "NOT_STARTED": "لم يبدأ",
    "IN_PROGRESS": "قيد التقييم",
    "COMPLIANT": "مستوفٍ",
    "PARTIALLY_COMPLIANT": "مستوفٍ جزئياً",
    "NON_COMPLIANT": "غير مستوفٍ",
}

# التسمية الصحيحة الجديدة لنفس الحالات: هذا تصنيف تغطية أدلة نصية داخلية
# (Evidence Coverage) فقط — ليس قرار امتثال (Compliance) رسمياً على مستوى
# مواصفة، وليس مستوى نضج (Maturity) رسمياً. لا تستخدم "COMPLIANT" وما
# شابهها في أي كود جديد يخص حالة السؤال (MQ)؛ استخدم هذه المفردات بدلاً
# منها.
EVIDENCE_STATUS_LABELS_AR = {
    "NOT_STARTED": "لم يبدأ",
    "IN_PROGRESS": "قيد التقييم",
    "EVIDENCE_PASS": "الأدلة مستوفاة",
    "EVIDENCE_PARTIAL": "الأدلة مستوفاة جزئياً",
    "EVIDENCE_FAIL": "الأدلة غير مستوفاة",
}

# خريطة تحويل من المفردات القديمة (Deprecated) إلى المفردات الجديدة
# الصحيحة، لتوليد الحقل الجديد evidence_status دون تكرار منطق العتبات.
_LEGACY_TO_EVIDENCE_STATUS = {
    "NOT_STARTED": "NOT_STARTED",
    "IN_PROGRESS": "IN_PROGRESS",
    "COMPLIANT": "EVIDENCE_PASS",
    "PARTIALLY_COMPLIANT": "EVIDENCE_PARTIAL",
    "NON_COMPLIANT": "EVIDENCE_FAIL",
}

# نفس عتبات PASS/PARTIAL_PASS المعتمدة في gap_analysis_engine.py، لضمان
# اتساق تصنيف تغطية الأدلة بين تقييم الدليل الواحد وحالة السؤال ككل. هذه
# عتبات هندسية داخلية لتصنيف تغطية الأدلة — وليست عتبات امتثال SDAIA رسمية
# (لا توجد أي عتبة رسمية موثّقة لهذا الغرض في مصدر نضيء المتاح).
MQ_EVIDENCE_COVERAGE_PASS_THRESHOLD = 90
MQ_EVIDENCE_COVERAGE_PARTIAL_THRESHOLD = 60


def _compute_mq_status(
    assessed_evidence: int, total_evidence: int, evidence_coverage_percentage: int
) -> str:
    """يشتق حالة تقدم واحدة للسؤال (MQ) من عدّادات مُحسَبة سلفاً.

    القيمة المُعادة بالمفردات القديمة (Deprecated، انظر MQ_STATUS_LABELS_AR)
    للحفاظ على التوافق الخلفي. استخدم _legacy_status_to_evidence_status()
    لتحويلها إلى المفردات الجديدة الصحيحة.
    """
    if assessed_evidence == 0:
        return "NOT_STARTED"
    if assessed_evidence < total_evidence:
        return "IN_PROGRESS"
    if evidence_coverage_percentage >= MQ_EVIDENCE_COVERAGE_PASS_THRESHOLD:
        return "COMPLIANT"
    if evidence_coverage_percentage >= MQ_EVIDENCE_COVERAGE_PARTIAL_THRESHOLD:
        return "PARTIALLY_COMPLIANT"
    return "NON_COMPLIANT"


def _legacy_status_to_evidence_status(legacy_status: str) -> str:
    """يحوّل قيمة mq_status القديمة (Deprecated) إلى evidence_status الجديدة الصحيحة."""
    return _LEGACY_TO_EVIDENCE_STATUS.get(legacy_status, legacy_status)


def _load_evidence_catalog(domain_code: str) -> List[Dict[str, Any]]:
    """يقرأ كل ملفات JSON داخل data/evidence_catalog/ ويستخرج عناصر الأدلة لكل MQ.

    يتجاهل أي ملف لا يحتوي على mq_id و evidence_items معاً (مثل ملف
    dc_evidence_catalog.json الذي هو دليل الدومين وليس فهرس أدلة).

    يُبقي فقط عناصر الأدلة التي يبدأ evidence_code فيها بـ "{domain_code}." — لأن
    كل ملفات evidence_catalog تعيش في مجلد مسطّح واحد، وقد يحتوي لاحقاً على
    دومينات أخرى غير DC.
    """
    catalog_entries: List[Dict[str, Any]] = []

    if not EVIDENCE_CATALOG_DIR.exists():
        return catalog_entries

    domain_prefix = f"{domain_code}."

    for file_path in sorted(EVIDENCE_CATALOG_DIR.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        if not isinstance(data, dict):
            continue

        mq_id = data.get("mq_id")
        evidence_items = data.get("evidence_items")

        if not mq_id or not isinstance(evidence_items, list):
            continue

        for item in evidence_items:
            code = item.get("code")
            name = item.get("name", "")
            if not code or not code.startswith(domain_prefix):
                continue
            catalog_entries.append(
                {
                    "evidence_code": code,
                    "evidence_name": name,
                    "mq_id": mq_id,
                }
            )

    return catalog_entries


def _normalize_assessment_result(raw_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """يوحّد شكل نتيجة تقييم واحدة (Orchestrator أو Dashboard Adapter) إلى شكل داخلي موحد:

    {
        "evidence_code": str,
        "status": "PASS" | "PARTIAL_PASS" | "FAIL" | "UNKNOWN",
        "coverage_percentage": float,
        "needs_human_review": bool,
    }
    """
    evidence_code = raw_result.get("evidence_code")
    if not evidence_code:
        return None

    if "combined_summary" in raw_result:
        assessment_status = raw_result.get("assessment_status")
        summary = raw_result.get("combined_summary") or {}

        if assessment_status == "file_read_failed":
            status = "UNKNOWN"
        else:
            status = summary.get("combined_overall_status", "UNKNOWN")

        coverage = summary.get("text_coverage_percentage", 0) or 0
        needs_human_review = bool(summary.get("needs_human_review", False))

    elif "assessment_available" in raw_result or "overall_status" in raw_result:
        if not raw_result.get("assessment_available", True):
            status = "UNKNOWN"
        else:
            status = raw_result.get("overall_status", "UNKNOWN")

        coverage = raw_result.get("coverage_percentage", 0) or 0
        needs_human_review = bool(raw_result.get("needs_human_review", False))

    else:
        status = raw_result.get("status", "UNKNOWN")
        coverage = raw_result.get("coverage_percentage", 0) or 0
        needs_human_review = bool(raw_result.get("needs_human_review", False))

    if status not in VALID_STATUSES:
        status = "UNKNOWN"

    return {
        "evidence_code": evidence_code,
        "status": status,
        "coverage_percentage": coverage,
        "needs_human_review": needs_human_review,
    }


def _build_evidence_result_map(
    assessment_results: List[Dict[str, Any]],
    warnings: List[str],
    known_codes: set,
) -> Dict[str, Dict[str, Any]]:
    """يوحّد ويطوي قائمة نتائج التقييم إلى خريطة evidence_code -> نتيجة موحدة.

    عند وجود أكثر من نتيجة لنفس الكود تُستخدم آخر نتيجة فقط.
    أكواد غير موجودة في الكتالوج تُستبعد وتُسجَّل في warnings.
    """
    result_map: Dict[str, Dict[str, Any]] = {}

    for raw_result in assessment_results:
        normalized = _normalize_assessment_result(raw_result)
        if normalized is None:
            continue

        evidence_code = normalized["evidence_code"]

        if evidence_code not in known_codes:
            warnings.append(
                f"تم تجاهل Evidence Code غير موجود في الكتالوج: {evidence_code}"
            )
            continue

        result_map[evidence_code] = normalized

    return result_map


def _compute_progress_stats(
    entries: List[Dict[str, Any]], result_map: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """يحسب إحصائيات التقدم (عدّادات، نسب اكتمال التقييم، ومتوسط تغطية الأدلة النصية)
    لمجموعة من عناصر الأدلة.

    ملاحظة تسمية: القيمة المُعادة تحت مفتاح evidence_coverage_percentage هي
    متوسط حسابي بسيط لـ coverage_percentage (تغطية نصية لكل دليل مفرد، من
    gap_analysis_engine.py) — وليست نسبة امتثال (Compliance) رسمية على
    مستوى مواصفة، وليست مدخلاً لأي حساب نضج (Maturity) رسمي.
    """
    total_evidence = len(entries)
    assessed_evidence = 0
    pass_count = 0
    partial_pass_count = 0
    fail_count = 0
    unknown_count = 0
    needs_human_review_count = 0
    coverage_sum = 0.0

    evidence_progress: List[Dict[str, Any]] = []

    for entry in entries:
        evidence_code = entry["evidence_code"]
        result = result_map.get(evidence_code)

        if result is None:
            status = "NOT_ASSESSED"
            coverage_percentage = 0
            assessed = False
            needs_human_review = False
        else:
            status = result["status"]
            coverage_percentage = result["coverage_percentage"]
            assessed = True
            needs_human_review = result["needs_human_review"]

        if assessed:
            assessed_evidence += 1
            if status == "PASS":
                pass_count += 1
            elif status == "PARTIAL_PASS":
                partial_pass_count += 1
            elif status == "FAIL":
                fail_count += 1
            elif status == "UNKNOWN":
                unknown_count += 1

        if needs_human_review:
            needs_human_review_count += 1

        coverage_sum += coverage_percentage

        evidence_progress.append(
            {
                "evidence_code": evidence_code,
                "evidence_name": entry["evidence_name"],
                "mq_id": entry["mq_id"],
                "status": status,
                "status_ar": STATUS_LABELS_AR[status],
                "coverage_percentage": coverage_percentage,
                "assessed": assessed,
                "needs_human_review": needs_human_review,
            }
        )

    not_assessed_evidence = total_evidence - assessed_evidence

    assessment_completion_percentage = (
        round(assessed_evidence / total_evidence * 100) if total_evidence else 0
    )
    evidence_coverage_percentage = (
        round(coverage_sum / total_evidence) if total_evidence else 0
    )

    return {
        "total_evidence": total_evidence,
        "assessed_evidence": assessed_evidence,
        "not_assessed_evidence": not_assessed_evidence,
        "pass_count": pass_count,
        "partial_pass_count": partial_pass_count,
        "fail_count": fail_count,
        "unknown_count": unknown_count,
        "assessment_completion_percentage": assessment_completion_percentage,
        "evidence_coverage_percentage": evidence_coverage_percentage,
        "needs_human_review_count": needs_human_review_count,
        "evidence_progress": evidence_progress,
    }


def calculate_domain_progress(
    assessment_results: List[Dict[str, Any]], domain_code: str = "DC"
) -> Dict[str, Any]:
    """يحسب تقدم المجال بالكامل انطلاقاً من نتائج تقييم بشكل Orchestrator (أو أي شكل موحّد آخر مدعوم).

    لا يشغّل أي تقييم فعلي، فقط يقرأ الكتالوج ويدمجه مع نتائج جاهزة.
    """
    warnings: List[str] = []

    entries = _load_evidence_catalog(domain_code)
    known_codes = {entry["evidence_code"] for entry in entries}

    result_map = _build_evidence_result_map(assessment_results, warnings, known_codes)

    domain_stats = _compute_progress_stats(entries, result_map)
    evidence_progress = domain_stats.pop("evidence_progress")

    entries_by_mq: Dict[str, List[Dict[str, Any]]] = {}
    for entry in entries:
        entries_by_mq.setdefault(entry["mq_id"], []).append(entry)

    mq_progress: List[Dict[str, Any]] = []
    for mq_id in sorted(entries_by_mq.keys()):
        mq_entries = entries_by_mq[mq_id]
        mq_stats = _compute_progress_stats(mq_entries, result_map)
        mq_stats.pop("evidence_progress")
        mq_stats.pop("needs_human_review_count")

        mq_status = _compute_mq_status(
            mq_stats["assessed_evidence"],
            mq_stats["total_evidence"],
            mq_stats["evidence_coverage_percentage"],
        )
        evidence_status = _legacy_status_to_evidence_status(mq_status)

        mq_progress.append(
            {
                "mq_id": mq_id,
                "total_evidence": mq_stats["total_evidence"],
                "assessed_evidence": mq_stats["assessed_evidence"],
                "not_assessed_evidence": mq_stats["not_assessed_evidence"],
                "pass_count": mq_stats["pass_count"],
                "partial_pass_count": mq_stats["partial_pass_count"],
                "fail_count": mq_stats["fail_count"],
                "unknown_count": mq_stats["unknown_count"],
                "assessment_completion_percentage": mq_stats[
                    "assessment_completion_percentage"
                ],
                # الحقول التالية محفوظة بلا تغيير (اسم وقيمة) لتوافق خلفي مع
                # src/dashboard/domain_progress_dashboard_adapter.py — انظر
                # ملاحظة MQ_STATUS_LABELS_AR أعلاه. لا تمثل قرار Compliance
                # رسمياً رغم اسمها.
                "compliance_percentage": mq_stats["evidence_coverage_percentage"],
                "mq_status": mq_status,
                "mq_status_ar": MQ_STATUS_LABELS_AR[mq_status],
                # الحقول الجديدة الصحيحة تسميةً — نفس القيم الحسابية تماماً.
                "evidence_coverage_percentage": mq_stats[
                    "evidence_coverage_percentage"
                ],
                "evidence_status": evidence_status,
                "evidence_status_ar": EVIDENCE_STATUS_LABELS_AR[evidence_status],
            }
        )

    return {
        "domain_code": domain_code,
        "domain_name": DOMAIN_NAMES_AR.get(domain_code, domain_code),
        "total_evidence": domain_stats["total_evidence"],
        "assessed_evidence": domain_stats["assessed_evidence"],
        "not_assessed_evidence": domain_stats["not_assessed_evidence"],
        "pass_count": domain_stats["pass_count"],
        "partial_pass_count": domain_stats["partial_pass_count"],
        "fail_count": domain_stats["fail_count"],
        "unknown_count": domain_stats["unknown_count"],
        "assessment_completion_percentage": domain_stats[
            "assessment_completion_percentage"
        ],
        # محفوظ بلا تغيير (اسم وقيمة) لتوافق خلفي — انظر ملاحظة أعلاه.
        "domain_compliance_percentage": domain_stats["evidence_coverage_percentage"],
        # الاسم الجديد الصحيح — نفس القيمة الحسابية تماماً.
        "domain_evidence_coverage_percentage": domain_stats[
            "evidence_coverage_percentage"
        ],
        "needs_human_review_count": domain_stats["needs_human_review_count"],
        "mq_progress": mq_progress,
        "evidence_progress": evidence_progress,
        "warnings": warnings,
    }


def calculate_domain_progress_from_dashboard_results(
    dashboard_results: List[Dict[str, Any]], domain_code: str = "DC"
) -> Dict[str, Any]:
    """نفس منطق calculate_domain_progress، لكن مخصصة لاستقبال نتائج بشكل Dashboard Adapter.

    التوحيد الفعلي بين الشكلين يتم داخل _normalize_assessment_result، لذلك هذه الدالة
    تستدعي المنطق الرئيسي مباشرة دون تكرار أي كود.
    """
    return calculate_domain_progress(dashboard_results, domain_code=domain_code)


def calculate_domain_progress_from_store(domain_code: str = "DC") -> Dict[str, Any]:
    """يحسب تقدم الدومين بالاعتماد على كل نتائج التقييم المحفوظة فعلياً في
    assessment_results_store، بدلاً من قائمة تُمرَّر يدوياً.

    هذه هي نقطة الدخول التي يُفترض أن يستخدمها Dashboard لاحقاً لعرض تقدم دومين
    كامل عبر كل الأدلة التي جرى تقييمها حتى الآن.
    """
    from src.scoring.assessment_results_store import load_assessment_results

    stored_results = load_assessment_results(domain_code)
    return calculate_domain_progress(stored_results, domain_code=domain_code)


def main() -> None:
    total_from_catalog = len(_load_evidence_catalog("DC"))

    print("=" * 60)
    print("الحالة 1: بدون أي نتائج تقييم")
    print("=" * 60)
    result_1 = calculate_domain_progress([], domain_code="DC")
    _print_result(result_1)
    assert result_1["total_evidence"] == total_from_catalog
    assert result_1["assessed_evidence"] == 0
    assert result_1["assessment_completion_percentage"] == 0
    assert result_1["domain_compliance_percentage"] == 0

    print()
    print("=" * 60)
    print("الحالة 2: نتيجة تقييم واحدة (DC.C.1.1 - PASS - 100%)")
    print("=" * 60)
    result_2 = calculate_domain_progress(
        [
            {
                "evidence_code": "DC.C.1.1",
                "assessment_status": "success",
                "combined_summary": {
                    "combined_overall_status": "PASS",
                    "text_coverage_percentage": 100,
                    "needs_human_review": False,
                },
            }
        ],
        domain_code="DC",
    )
    _print_result(result_2)
    assert result_2["assessed_evidence"] == 1
    assert result_2["pass_count"] == 1
    assert result_2["not_assessed_evidence"] == total_from_catalog - 1

    print()
    print("=" * 60)
    print("الحالة 3: ثلاث نتائج تقييم (PASS / PARTIAL_PASS / FAIL)")
    print("=" * 60)
    result_3 = calculate_domain_progress(
        [
            {
                "evidence_code": "DC.C.1.1",
                "assessment_status": "success",
                "combined_summary": {
                    "combined_overall_status": "PASS",
                    "text_coverage_percentage": 100,
                    "needs_human_review": False,
                },
            },
            {
                "evidence_code": "DC.M.2",
                "assessment_status": "success",
                "combined_summary": {
                    "combined_overall_status": "PARTIAL_PASS",
                    "text_coverage_percentage": 70,
                    "needs_human_review": True,
                },
            },
            {
                "evidence_code": "DC.M.3",
                "assessment_status": "success",
                "combined_summary": {
                    "combined_overall_status": "FAIL",
                    "text_coverage_percentage": 40,
                    "needs_human_review": False,
                },
            },
        ],
        domain_code="DC",
    )
    _print_result(result_3)
    assert result_3["assessed_evidence"] == 3
    assert result_3["pass_count"] == 1
    assert result_3["partial_pass_count"] == 1
    assert result_3["fail_count"] == 1

    print()
    print("=" * 60)
    print("الحالة 4: كود غير معروف (DC.FAKE.999)")
    print("=" * 60)
    result_4 = calculate_domain_progress(
        [
            {
                "evidence_code": "DC.FAKE.999",
                "assessment_status": "success",
                "combined_summary": {
                    "combined_overall_status": "PASS",
                    "text_coverage_percentage": 100,
                    "needs_human_review": False,
                },
            }
        ],
        domain_code="DC",
    )
    _print_result(result_4)
    assert result_4["assessed_evidence"] == 0
    assert len(result_4["warnings"]) == 1


def _print_result(result: Dict[str, Any]) -> None:
    print(f"total_evidence: {result['total_evidence']}")
    print(f"assessed_evidence: {result['assessed_evidence']}")
    print(f"not_assessed_evidence: {result['not_assessed_evidence']}")
    print(f"pass_count: {result['pass_count']}")
    print(f"partial_pass_count: {result['partial_pass_count']}")
    print(f"fail_count: {result['fail_count']}")
    print(f"unknown_count: {result['unknown_count']}")
    print(f"assessment_completion_percentage: {result['assessment_completion_percentage']}%")
    print(f"domain_compliance_percentage: {result['domain_compliance_percentage']}%")
    print(f"needs_human_review_count: {result['needs_human_review_count']}")
    print(f"عدد MQs: {len(result['mq_progress'])}")
    print(f"warnings: {result['warnings']}")

    print("ملخص كل MQ:")
    for mq in result["mq_progress"]:
        print(
            f"  - {mq['mq_id']}: total_evidence={mq['total_evidence']}, "
            f"assessed_evidence={mq['assessed_evidence']}, "
            f"compliance_percentage={mq['compliance_percentage']}%"
        )


if __name__ == "__main__":
    main()
