"""
Domain Progress Validator — يتحقق من أن domain_progress_engine.py ينتج تقدم دومين
سليم البنية ومتّسق حسابياً، عبر حالات اختبار ثابتة (Fixed Test Cases) معروفة النتيجة
مسبقاً.

لا يُستخدم أي LLM ولا LangChain ولا أي API خارجي هنا — فقط استدعاءات مباشرة
لدالة calculate_domain_progress من src/scoring/domain_progress_engine.py ومقارنة
نصية/رقمية بسيطة للنتائج.

ملاحظة: الحقل الفعلي لحالة السؤال (MQ) في مخرجات المحرك هو mq_status/mq_status_ar
(انظر domain_progress_engine.py) وليس status/status_ar — هذا المدقق يتحقق من الشكل
الحقيقي الذي ينتجه المحرك فعلياً، مع قبول status/status_ar كاسم بديل احتياطياً.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.scoring.domain_progress_engine import (
    _compute_mq_status,
    calculate_domain_progress,
)

REPORT_PATH = PROJECT_ROOT / "reports" / "domain_progress_validation_report.txt"

REQUIRED_DOMAIN_FIELDS = (
    "domain_code",
    "domain_name",
    "total_evidence",
    "assessed_evidence",
    "assessment_completion_percentage",
    "domain_compliance_percentage",
    "mq_progress",
    "warnings",
)

# كل عنصر هنا اسم واحد أو (الاسم الحقيقي في المحرك, اسم بديل مقبول احتياطياً).
REQUIRED_MQ_FIELDS = (
    "mq_id",
    ("mq_status", "status"),
    ("mq_status_ar", "status_ar"),
    "compliance_percentage",
    "assessment_completion_percentage",
    "assessed_evidence",
    "total_evidence",
)


def _mq_label(mq: dict[str, Any]) -> str:
    return mq.get("mq_id") or "<unknown>"


def _get_field(mq: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in mq:
            return mq[name]
    return None


def _has_field(mq: dict[str, Any], names: tuple[str, ...]) -> bool:
    return any(name in mq for name in names)


@dataclass
class ValidationResult:
    """نتيجة التحقق الكاملة من مخرجات domain_progress_engine."""

    passed: bool
    domain_name: str
    structure_passed: bool
    percentage_passed: bool
    status_passed: bool
    consistency_passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_structure(progress: Any) -> list[str]:
    """1. Structure Validation — الحقول المطلوبة على مستوى الدومين وكل MQ."""
    if not isinstance(progress, dict):
        return [f"Invalid progress type: expected dict, got {type(progress).__name__}"]

    errors: list[str] = []
    for field_name in REQUIRED_DOMAIN_FIELDS:
        if field_name not in progress:
            errors.append(f"Missing field: {field_name}")

    if "mq_progress" not in progress:
        return errors

    mq_progress = progress["mq_progress"]
    if not isinstance(mq_progress, list):
        errors.append(f"Invalid field type: mq_progress must be a list, got {type(mq_progress).__name__}")
        return errors

    for index, mq in enumerate(mq_progress):
        if not isinstance(mq, dict):
            errors.append(f"Invalid MQ entry at index {index}: expected dict, got {type(mq).__name__}")
            continue
        label = _mq_label(mq) if mq.get("mq_id") else f"index {index}"
        for field_spec in REQUIRED_MQ_FIELDS:
            names = field_spec if isinstance(field_spec, tuple) else (field_spec,)
            if not _has_field(mq, names):
                errors.append(f"Missing field in MQ ({label}): {names[0]}")

    return errors


def validate_data_integrity(progress: dict[str, Any]) -> list[str]:
    """2. Data Integrity Validation — نطاقات النسب، القيم السالبة، والأكواد الفارغة."""
    errors: list[str] = []

    if not progress.get("domain_code"):
        errors.append("Missing or empty domain_code")

    for pct_field in ("assessment_completion_percentage", "domain_compliance_percentage"):
        value = progress.get(pct_field)
        if isinstance(value, (int, float)) and not (0 <= value <= 100):
            errors.append(f"Invalid percentage {pct_field}={value} (must be between 0 and 100)")

    total_evidence = progress.get("total_evidence")
    assessed_evidence = progress.get("assessed_evidence")
    if isinstance(total_evidence, int) and total_evidence < 0:
        errors.append(f"Negative value: total_evidence={total_evidence}")
    if isinstance(assessed_evidence, int) and assessed_evidence < 0:
        errors.append(f"Negative value: assessed_evidence={assessed_evidence}")
    if (
        isinstance(total_evidence, int)
        and isinstance(assessed_evidence, int)
        and assessed_evidence > total_evidence
    ):
        errors.append(
            f"assessed_evidence ({assessed_evidence}) exceeds total_evidence ({total_evidence})"
        )

    for mq in progress.get("mq_progress") or []:
        if not isinstance(mq, dict):
            continue
        label = _mq_label(mq)
        if not mq.get("mq_id"):
            errors.append("MQ entry has empty mq_id")

        for pct_field in ("compliance_percentage", "assessment_completion_percentage"):
            value = mq.get(pct_field)
            if isinstance(value, (int, float)) and not (0 <= value <= 100):
                errors.append(f"Invalid percentage in MQ ({label}): {pct_field}={value}")

        mq_total = mq.get("total_evidence")
        mq_assessed = mq.get("assessed_evidence")
        if isinstance(mq_total, int) and mq_total < 0:
            errors.append(f"Negative value in MQ ({label}): total_evidence={mq_total}")
        if isinstance(mq_assessed, int) and mq_assessed < 0:
            errors.append(f"Negative value in MQ ({label}): assessed_evidence={mq_assessed}")
        if isinstance(mq_total, int) and isinstance(mq_assessed, int) and mq_assessed > mq_total:
            errors.append(
                f"MQ ({label}): assessed_evidence ({mq_assessed}) exceeds total_evidence ({mq_total})"
            )

    return errors


def validate_status_logic(progress: dict[str, Any]) -> list[str]:
    """3. Status Logic Validation — يعيد استخدام _compute_mq_status الحقيقية من المحرك
    كمرجع وحيد للحقيقة، بدل تكرار نسخة موازية من قواعد الحالة قد تنحرف عنها لاحقاً."""
    errors: list[str] = []

    for mq in progress.get("mq_progress") or []:
        if not isinstance(mq, dict):
            continue
        label = _mq_label(mq)
        assessed = mq.get("assessed_evidence")
        total = mq.get("total_evidence")
        compliance = mq.get("compliance_percentage")
        actual_status = _get_field(mq, ("mq_status", "status"))

        if not isinstance(assessed, int) or not isinstance(total, int) or not isinstance(compliance, (int, float)):
            continue  # نوع الحقل غير صالح أصلاً — مُبلَّغ عنه في integrity/structure

        expected_status = _compute_mq_status(assessed, total, compliance)
        if actual_status != expected_status:
            errors.append(
                f"Incorrect status in MQ ({label}): expected={expected_status} actual={actual_status}"
            )

    return errors


def validate_calculation_consistency(progress: dict[str, Any]) -> list[str]:
    """4. Calculation Consistency Validation — assessment_completion_percentage يجب أن
    يساوي round(assessed_evidence / total_evidence * 100)، على مستوى الدومين وكل MQ."""
    errors: list[str] = []

    total = progress.get("total_evidence")
    assessed = progress.get("assessed_evidence")
    completion = progress.get("assessment_completion_percentage")
    if isinstance(total, int) and isinstance(assessed, int) and isinstance(completion, (int, float)):
        expected = round(assessed / total * 100) if total else 0
        if completion != expected:
            errors.append(
                f"Inconsistent assessment_completion_percentage: expected={expected} actual={completion}"
            )

    for mq in progress.get("mq_progress") or []:
        if not isinstance(mq, dict):
            continue
        label = _mq_label(mq)
        mq_total = mq.get("total_evidence")
        mq_assessed = mq.get("assessed_evidence")
        mq_completion = mq.get("assessment_completion_percentage")
        if (
            isinstance(mq_total, int)
            and isinstance(mq_assessed, int)
            and isinstance(mq_completion, (int, float))
        ):
            expected = round(mq_assessed / mq_total * 100) if mq_total else 0
            if mq_completion != expected:
                errors.append(
                    f"Inconsistent assessment_completion_percentage in MQ ({label}): "
                    f"expected={expected} actual={mq_completion}"
                )

    return errors


def validate_domain_progress(progress: Any) -> ValidationResult:
    """نقطة الدخول الرئيسية: يشغّل الفحوصات الأربعة بالترتيب على مخرجات
    calculate_domain_progress ويعيد ValidationResult واحدة موحّدة."""
    structure_errors = validate_structure(progress)
    if structure_errors:
        # لا معنى لتشغيل فحوصات النسب/الحالة/الاتساق على بنية مكسورة أصلاً —
        # قد تصل لحقول مفقودة وتنهار بأخطاء لا علاقة لها بالمشكلة الحقيقية.
        domain_name = progress.get("domain_name", "<unknown>") if isinstance(progress, dict) else "<unknown>"
        warnings = list(progress.get("warnings", [])) if isinstance(progress, dict) else []
        return ValidationResult(
            passed=False,
            domain_name=domain_name,
            structure_passed=False,
            percentage_passed=False,
            status_passed=False,
            consistency_passed=False,
            errors=structure_errors,
            warnings=warnings,
        )

    integrity_errors = validate_data_integrity(progress)
    status_errors = validate_status_logic(progress)
    consistency_errors = validate_calculation_consistency(progress)
    all_errors = integrity_errors + status_errors + consistency_errors

    return ValidationResult(
        passed=not all_errors,
        domain_name=progress.get("domain_name", "<unknown>"),
        structure_passed=True,
        percentage_passed=not integrity_errors,
        status_passed=not status_errors,
        consistency_passed=not consistency_errors,
        errors=all_errors,
        warnings=list(progress.get("warnings", [])),
    )


def build_validation_report(result: ValidationResult) -> str:
    """5. Output Report — تقرير مقروء بنفس روح المدققات الأخرى."""
    lines: list[str] = []
    lines.append("=" * 50)
    lines.append("Domain Progress Validation Report")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Status: {'PASSED' if result.passed else 'FAILED'}")
    lines.append("")
    lines.append("Domain:")
    lines.append(result.domain_name)
    lines.append("")
    lines.append("Checks:")
    lines.append(f"{'✓' if result.structure_passed else '✗'} Structure validation")
    lines.append(f"{'✓' if result.percentage_passed else '✗'} Percentage validation")
    lines.append(f"{'✓' if result.status_passed else '✗'} MQ status validation")
    lines.append(f"{'✓' if result.consistency_passed else '✗'} Calculation consistency")
    lines.append("")

    if not result.passed:
        lines.append("List:")
        for error in result.errors:
            lines.append(f"- {error}")
        lines.append("")

    lines.append("Warnings:")
    if result.warnings:
        for warning in result.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("None")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Fixed Test Cases
# ---------------------------------------------------------------------------


def _build_valid_progress() -> dict[str, Any]:
    """يبني مخرجات حقيقية من calculate_domain_progress على أكواد أدلة معروفة
    (نفس الأكواد المستخدمة في domain_progress_engine.main())، لا بيانات مصطنعة."""
    return calculate_domain_progress(
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
        ],
        domain_code="DC",
    )


def _expect(
    progress: dict[str, Any], expect_passed: bool, expect_error_substring: str | None = None
) -> tuple[ValidationResult, list[str]]:
    result = validate_domain_progress(progress)
    mismatches: list[str] = []
    if result.passed != expect_passed:
        mismatches.append(f"passed: expected={expect_passed} actual={result.passed}")
    if expect_error_substring is not None and not any(
        expect_error_substring in error for error in result.errors
    ):
        mismatches.append(
            f"expected an error containing {expect_error_substring!r}, got: {result.errors}"
        )
    return result, mismatches


def test_valid_domain_progress():
    """1. Valid domain progress output — يجب أن يجتاز كل الفحوصات الأربعة."""
    progress = _build_valid_progress()
    result, mismatches = _expect(progress, expect_passed=True)
    return {
        "name": "Valid Domain Progress",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [f"errors={result.errors}", f"warnings={result.warnings}"],
        "report": build_validation_report(result),
    }


def test_missing_field():
    """2. Missing field — حذف domain_compliance_percentage يجب أن يُفشل Structure validation."""
    progress = copy.deepcopy(_build_valid_progress())
    del progress["domain_compliance_percentage"]
    result, mismatches = _expect(
        progress, expect_passed=False, expect_error_substring="Missing field: domain_compliance_percentage"
    )
    return {
        "name": "Missing Field",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [f"errors={result.errors}"],
        "report": build_validation_report(result),
    }


def test_invalid_percentage():
    """3. Invalid percentage — domain_compliance_percentage=150 يجب أن يُفشل Percentage validation."""
    progress = copy.deepcopy(_build_valid_progress())
    progress["domain_compliance_percentage"] = 150
    result, mismatches = _expect(progress, expect_passed=False, expect_error_substring="Invalid percentage")
    return {
        "name": "Invalid Percentage",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [f"errors={result.errors}"],
        "report": build_validation_report(result),
    }


def test_incorrect_status():
    """4. Incorrect status — إجبار mq_status على قيمة تناقض assessed/total/compliance
    يجب أن يُفشل MQ status validation."""
    progress = copy.deepcopy(_build_valid_progress())
    mq_progress = progress["mq_progress"]
    if not mq_progress:
        return {
            "name": "Incorrect Status",
            "passed": False,
            "reason": "no MQs available in catalog to corrupt",
            "details": [],
            "report": "",
        }
    target_mq = mq_progress[0]
    target_mq["mq_status"] = (
        "COMPLIANT" if target_mq["mq_status"] != "COMPLIANT" else "NON_COMPLIANT"
    )
    result, mismatches = _expect(progress, expect_passed=False, expect_error_substring="Incorrect status")
    return {
        "name": "Incorrect Status",
        "passed": not mismatches,
        "reason": "; ".join(mismatches),
        "details": [f"errors={result.errors}"],
        "report": build_validation_report(result),
    }


TEST_FUNCS = [
    test_valid_domain_progress,
    test_missing_field,
    test_invalid_percentage,
    test_incorrect_status,
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
                "report": "",
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
    lines.append("تقرير التحقق من Domain Progress Engine")
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
        if outcome["report"]:
            lines.append("")
            lines.append("    Generated report for this case:")
            for report_line in outcome["report"].splitlines():
                lines.append(f"    {report_line}")

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
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
