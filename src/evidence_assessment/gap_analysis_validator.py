"""
Gap Analysis Validator — يتحقق من أن gap_analysis_engine.py يطبق قواعد التقييم
الصارمة (Mandatory Gate / Critical / Coverage / Overall Status) بشكل صحيح، عبر
حالات اختبار ثابتة (Fixed Test Cases) معروفة النتيجة مسبقاً.

لا يُستخدم أي LLM ولا LangChain ولا أي API خارجي هنا — فقط استدعاءات مباشرة
لدوال src/evidence_assessment/gap_analysis_engine.py ومقارنة نصية بسيطة للنتائج.
"""

import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.evidence_assessment.gap_analysis_engine import analyze_gap, analyze_multiple

REPORT_PATH = PROJECT_ROOT / "reports" / "gap_analysis_validation_report.txt"


def _compare_fields(result, expected_fields):
    """يقارن حقولاً محددة من النتيجة بقيمها المتوقعة، ويعيد قائمة رسائل الفروقات (فارغة = تطابق)."""
    mismatches = []
    for key, expected_value in expected_fields.items():
        actual_value = result.get(key)
        if actual_value != expected_value:
            mismatches.append(f"{key}: expected={expected_value!r} actual={actual_value!r}")
    return mismatches


def test_empty_evidence():
    """1. Empty Evidence — analyze_gap('DC.M.6', '') يجب أن يعطي NOT_PROVIDED."""
    result = analyze_gap("DC.M.6", "")
    mismatches = _compare_fields(result, {
        "overall_status": "NOT_PROVIDED",
        "mandatory_requirement_passed": False,
    })
    return {
        "name": "Empty Evidence",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"overall_status={result['overall_status']}",
            f"mandatory_requirement_passed={result['mandatory_requirement_passed']}",
        ],
    }


def test_mandatory_missing():
    """2. Mandatory Missing — نص لا يحتوي required_terms الأساسية لـ DC.M.6."""
    text = "هذا مستند عام يحتوي على معلومات عن البيانات فقط"
    result = analyze_gap("DC.M.6", text)
    mismatches = _compare_fields(result, {
        "overall_status": "FAIL",
        "mandatory_requirement_passed": False,
    })
    return {
        "name": "Mandatory Missing",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"overall_status={result['overall_status']}",
            f"mandatory_requirement_passed={result['mandatory_requirement_passed']}",
        ],
    }


def test_mandatory_pass_critical_missing():
    """3. Mandatory Pass But Critical Missing — نص يحقق mandatory لكن ينقصه critical criteria."""
    text = "سياسة تصنيف البيانات معتمدة من صاحب الصلاحية وتتضمن نطاق العمل وتاريخ الإصدار"
    result = analyze_gap("DC.M.6", text)
    mismatches = _compare_fields(result, {
        "mandatory_requirement_passed": True,
        "overall_status": "FAIL",
    })
    if not result.get("critical_missing"):
        mismatches.append("critical_missing: expected=non-empty actual=empty")
    return {
        "name": "Mandatory Pass But Critical Missing",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"mandatory_requirement_passed={result['mandatory_requirement_passed']}",
            f"overall_status={result['overall_status']}",
            f"critical_missing={result['critical_missing']}",
        ],
    }


def test_partial_pass():
    """4. Partial Pass — DC.C.5.1 بنص يحقق mandatory ولا يفشل أي critical."""
    text = "سجل البيانات يحتوي قائمة مجموعات البيانات والسجلات المحددة ومستويات التصنيف الممنوحة"
    result = analyze_gap("DC.C.5.1", text)
    mismatches = _compare_fields(result, {
        "mandatory_requirement_passed": True,
        "overall_status": "PARTIAL_PASS",
    })
    return {
        "name": "Partial Pass",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"mandatory_requirement_passed={result['mandatory_requirement_passed']}",
            f"overall_status={result['overall_status']}",
            f"coverage_percentage={result['coverage_percentage']}",
            f"critical_missing={result['critical_missing']}",
        ],
    }


def test_unknown_evidence():
    """5. Unknown Evidence — analyze_gap('DC.NOT.REAL', ...) يجب أن يفشل ويحتاج مراجعة بشرية."""
    result = analyze_gap("DC.NOT.REAL", "أي نص")
    mismatches = _compare_fields(result, {
        "overall_status": "FAIL",
        "needs_human_review": True,
    })
    return {
        "name": "Unknown Evidence",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"overall_status={result['overall_status']}",
            f"needs_human_review={result['needs_human_review']}",
        ],
    }


def test_analyze_multiple():
    """6. analyze_multiple — يجب أن يعيد قائمة نتائج بنفس عدد الأكواد المُدخلة."""
    codes = ["DC.M.6", "DC.C.5.1", "DC.NOT.REAL"]
    provided_map = {
        "DC.M.6": "",
        "DC.C.5.1": "سجل البيانات يحتوي قائمة مجموعات البيانات والسجلات المحددة",
    }
    results = analyze_multiple(codes, provided_map)
    mismatches = []
    if len(results) != len(codes):
        mismatches.append(f"length: expected={len(codes)} actual={len(results)}")
    else:
        for code, result in zip(codes, results):
            if result.get("evidence_code") != code:
                mismatches.append(f"order mismatch: expected={code!r} actual={result.get('evidence_code')!r}")
    return {
        "name": "analyze_multiple",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [
            f"input_codes_count={len(codes)}",
            f"returned_results_count={len(results)}",
        ],
    }


TEST_FUNCS = [
    test_empty_evidence,
    test_mandatory_missing,
    test_mandatory_pass_critical_missing,
    test_partial_pass,
    test_unknown_evidence,
    test_analyze_multiple,
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


def _print_test_result(outcome):
    status = "PASS" if outcome["passed"] else "FAIL"
    print(f"{outcome['name']}: {status}")
    if not outcome["passed"]:
        print(f"  السبب: {outcome['reason']}")


def _write_report(test_results, passed_count, failed_count, overall_result):
    lines = []
    lines.append("=" * 70)
    lines.append("تقرير التحقق من Gap Analysis Engine")
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

    for outcome in test_results:
        _print_test_result(outcome)

    passed_count = sum(1 for r in test_results if r["passed"])
    failed_count = len(test_results) - passed_count
    overall_result = "PASS" if failed_count == 0 else "FAIL"

    _write_report(test_results, passed_count, failed_count, overall_result)

    print(f"\nعدد PASS: {passed_count}")
    print(f"عدد FAIL: {failed_count}")
    print(f"Overall Result: {overall_result}")


if __name__ == "__main__":
    main()
