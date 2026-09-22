"""
Compliance Recommendation Validator — يتحقق من أن compliance_recommendation_engine.py
يولّد توصيات صحيحة بناءً على نتائج Gap Analysis، عبر حالات اختبار ثابتة
(Fixed Test Cases) معروفة النتيجة مسبقاً.

لا يُستخدم أي LLM ولا LangChain ولا أي API خارجي هنا — فقط استدعاءات مباشرة
لدالة generate_recommendations من src/recommendations/compliance_recommendation_engine.py
ومقارنة نصية/رقمية بسيطة للنتائج.
"""

import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendations.compliance_recommendation_engine import generate_recommendations

REPORT_PATH = PROJECT_ROOT / "reports" / "compliance_recommendation_validation_report.txt"

REQUIRED_RECOMMENDATION_KEYS = {
    "evidence_code",
    "overall_status",
    "priority",
    "recommendation_type",
    "issue",
    "action",
    "impact",
    "references",
    "supporting_documents",
}

REQUIRED_ISSUE_KEYS = {"criterion", "reason", "category"}
REQUIRED_ACTION_KEYS = {"title", "description"}
REQUIRED_IMPACT_KEYS = {"severity", "expected_improvement"}

VALID_PRIORITIES = {"HIGH", "MEDIUM"}


def _check_recommendation_shape(recommendations):
    """يتحقق أن كل توصية (Structured Recommendation Object) تطابق البنية الجديدة
    كاملة، ويعيد قائمة رسائل الفروقات."""
    mismatches = []
    for index, rec in enumerate(recommendations):
        prefix = f"recommendation[{index}]"

        missing_keys = REQUIRED_RECOMMENDATION_KEYS - rec.keys()
        if missing_keys:
            mismatches.append(f"{prefix} missing keys: {sorted(missing_keys)}")
            continue

        issue = rec.get("issue") or {}
        missing_issue_keys = REQUIRED_ISSUE_KEYS - issue.keys()
        if missing_issue_keys:
            mismatches.append(f"{prefix}.issue missing keys: {sorted(missing_issue_keys)}")

        action = rec.get("action") or {}
        missing_action_keys = REQUIRED_ACTION_KEYS - action.keys()
        if missing_action_keys:
            mismatches.append(f"{prefix}.action missing keys: {sorted(missing_action_keys)}")

        impact = rec.get("impact") or {}
        missing_impact_keys = REQUIRED_IMPACT_KEYS - impact.keys()
        if missing_impact_keys:
            mismatches.append(f"{prefix}.impact missing keys: {sorted(missing_impact_keys)}")

        priority = rec.get("priority")
        if priority not in VALID_PRIORITIES:
            mismatches.append(f"{prefix}.priority: expected HIGH/MEDIUM actual={priority!r}")

        severity = impact.get("severity")
        if severity != priority:
            mismatches.append(
                f"{prefix}.impact.severity: expected={priority!r} actual={severity!r}"
            )

        if not action.get("description"):
            mismatches.append(f"{prefix}.action.description: expected non-empty")

        if not issue.get("reason"):
            mismatches.append(f"{prefix}.issue.reason: expected non-empty")

        if not isinstance(rec.get("supporting_documents"), list):
            mismatches.append(
                f"{prefix}.supporting_documents: expected list actual={type(rec.get('supporting_documents')).__name__}"
            )

        if not isinstance(rec.get("references"), list):
            mismatches.append(
                f"{prefix}.references: expected list actual={type(rec.get('references')).__name__}"
            )

    return mismatches


def test_dc_m6():
    """1. DC.M.6 — نص يحقق mandatory لكن ينقصه critical/medium criteria كثيرة."""
    text = "سياسة تصنيف البيانات معتمدة من صاحب الصلاحية وتتضمن نطاق العمل وتاريخ الإصدار"
    output = generate_recommendations("DC.M.6", text)
    summary = output["summary"]
    recommendations = output["recommendations"]

    mismatches = []
    if summary["overall_status"] != "FAIL":
        mismatches.append(f"overall_status: expected=FAIL actual={summary['overall_status']!r}")
    if not summary["total_recommendations"] > 0:
        mismatches.append(f"total_recommendations: expected>0 actual={summary['total_recommendations']}")
    if not summary["high_priority_count"] > 0:
        mismatches.append(f"high_priority_count: expected>0 actual={summary['high_priority_count']}")
    if not any(rec["priority"] == "HIGH" for rec in recommendations):
        mismatches.append("expected at least one recommendation with priority=HIGH")
    mismatches.extend(_check_recommendation_shape(recommendations))

    return {
        "name": "DC.M.6",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"overall_status={summary['overall_status']}",
            f"total_recommendations={summary['total_recommendations']}",
            f"high_priority_count={summary['high_priority_count']}",
            f"medium_priority_count={summary['medium_priority_count']}",
        ],
    }


def test_dc_c5_1():
    """2. DC.C.5.1 — نص يحقق mandatory ولا يفشل أي critical (PARTIAL_PASS بضبط عددين متوسطين)."""
    text = "سجل البيانات يحتوي قائمة مجموعات البيانات والسجلات المحددة ومستويات التصنيف الممنوحة"
    output = generate_recommendations("DC.C.5.1", text)
    summary = output["summary"]

    mismatches = []
    if summary["overall_status"] != "PARTIAL_PASS":
        mismatches.append(f"overall_status: expected=PARTIAL_PASS actual={summary['overall_status']!r}")
    if summary["total_recommendations"] != 2:
        mismatches.append(f"total_recommendations: expected=2 actual={summary['total_recommendations']}")
    if summary["high_priority_count"] != 0:
        mismatches.append(f"high_priority_count: expected=0 actual={summary['high_priority_count']}")
    if summary["medium_priority_count"] != 2:
        mismatches.append(f"medium_priority_count: expected=2 actual={summary['medium_priority_count']}")
    mismatches.extend(_check_recommendation_shape(output["recommendations"]))

    return {
        "name": "DC.C.5.1",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"overall_status={summary['overall_status']}",
            f"total_recommendations={summary['total_recommendations']}",
            f"high_priority_count={summary['high_priority_count']}",
            f"medium_priority_count={summary['medium_priority_count']}",
        ],
    }


def test_unknown_evidence():
    """3. DC.NOT.REAL — دليل غير معروف: يجب ألا يرمي Exception، ويعيد summary مع needs_human_review=True."""
    try:
        output = generate_recommendations("DC.NOT.REAL", "أي نص")
    except Exception as exc:
        return {
            "name": "Unknown Evidence (DC.NOT.REAL)",
            "passed": False,
            "reason": f"Exception raised: {exc}",
            "details": [],
        }

    mismatches = []
    summary = output.get("summary")
    if summary is None:
        mismatches.append("summary: expected=dict actual=None")
    elif not summary.get("needs_human_review"):
        mismatches.append(f"needs_human_review: expected=True actual={summary.get('needs_human_review')!r}")

    return {
        "name": "Unknown Evidence (DC.NOT.REAL)",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"summary_present={summary is not None}",
            f"needs_human_review={summary.get('needs_human_review') if summary else None}",
        ],
    }


TEST_FUNCS = [
    test_dc_m6,
    test_dc_c5_1,
    test_unknown_evidence,
]


def _run_all_tests():
    test_results = []
    for test_func in TEST_FUNCS:
        try:
            outcome = test_func()
        except Exception as exc:
            outcome = {
                "name": test_func.__name__,
                "passed": False,
                "reason": f"Exception: {exc}",
                "details": [],
            }
        test_results.append(outcome)
    return test_results


def _write_report(test_results, passed_count, failed_count, overall_result):
    lines = []
    lines.append("=" * 70)
    lines.append("تقرير التحقق من Compliance Recommendation Engine")
    lines.append("=" * 70)
    lines.append(f"عدد الاختبارات: {len(test_results)}")
    lines.append(f"عدد PASS: {passed_count}")
    lines.append(f"عدد FAIL: {failed_count}")
    lines.append(f"النتيجة النهائية: {overall_result}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("تفاصيل الاختبارات")
    lines.append("-" * 70)

    for outcome in test_results:
        status = "PASS" if outcome["passed"] else "FAIL"
        lines.append(f"\n[{status}] {outcome['name']}")
        for detail in outcome["details"]:
            lines.append(f"    {detail}")
        if not outcome["passed"]:
            lines.append(f"    السبب: {outcome['reason']}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    test_results = _run_all_tests()

    passed_count = sum(1 for r in test_results if r["passed"])
    failed_count = len(test_results) - passed_count
    overall_result = "PASS" if failed_count == 0 else "FAIL"

    _write_report(test_results, passed_count, failed_count, overall_result)

    print(f"عدد PASS: {passed_count}")
    print(f"عدد FAIL: {failed_count}")
    print(f"Overall Result: {overall_result}")


if __name__ == "__main__":
    main()
