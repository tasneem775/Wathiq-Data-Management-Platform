"""Phase 3 quality checker for Data Classification (DC) maturity model JSON files.

Reads the DC maturity model files, validates their structure against the
expected AI Compliance Engine schema, checks evidence codes and text content,
and prints a per-file quality report. Does not modify any JSON file.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

MATURITY_MODEL_FILE_NAMES = ["DC_MQ_1.json", "DC_MQ_2.json", "DC_MQ_3.json"]
EXPECTED_LEVEL_NUMBERS = [0, 1, 2, 3, 4, 5]

TOP_LEVEL_EXPECTED_FIELDS = ["mq_id", "domain_code", "domain_name_ar", "levels"]
LEVEL_EXPECTED_FIELDS = ["level_number", "level_name", "evidence"]
EVIDENCE_EXPECTED_FIELDS = ["evidence_name", "evidence_code", "acceptance_criteria", "related_specifications"]

# Unified schema field names (after the DC schema normalization pass).
LEVEL_NUMBER_KEY = "level_number"
LEVEL_NAME_KEY = "level_name"
EVIDENCE_LIST_KEY = "evidence"
EVIDENCE_CODE_KEY = "evidence_code"
EVIDENCE_NAME_KEY = "evidence_name"
EVIDENCE_ACCEPTANCE_CRITERIA_KEY = "acceptance_criteria"

VALID_CODE_PATTERN = re.compile(r"^DC\.(M\.\d+|C\.\d+\.\d+)$")

COMMON_SHORT_ARABIC_WORDS = {
    "و", "في", "من", "لا", "ما", "أن", "إن", "لم", "لن", "أو", "بل",
    "قد", "كي", "لك", "به", "له", "هو", "هي", "ثم", "يا", "قط", "عن",
}
SUSPICIOUS_TOKEN_PATTERN = re.compile(r"(?<![ء-ي])[ء-ي]{1,2}(?![ء-ي])")


class FileReport:
    """Collects quality findings for a single maturity model file."""

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        self.level_count = 0
        self.evidence_count = 0
        self.code_count = 0
        self.critical_errors: list[str] = []
        self.warnings: list[str] = []
        self.recommendations: list[str] = []

    def add_critical(self, message: str) -> None:
        self.critical_errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_recommendation(self, message: str) -> None:
        self.recommendations.append(message)


def _load_json_file(file_path: Path) -> dict[str, Any] | None:
    """Loads a JSON file as UTF-8 text.

    Returns:
        The parsed JSON object, or None if the file could not be read/parsed.
    """
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def _check_top_level_fields(data: dict[str, Any], report: FileReport) -> None:
    for field_name in TOP_LEVEL_EXPECTED_FIELDS:
        if field_name not in data:
            report.add_critical(f"الحقل الأساسي '{field_name}' غير موجود في مستوى الملف")

    if not data.get("mq_id"):
        report.add_critical("قيمة mq_id فارغة")


def _check_levels_coverage(levels: list[dict[str, Any]], report: FileReport) -> None:
    level_numbers: list[int] = []
    for level in levels:
        if LEVEL_NUMBER_KEY not in level:
            report.add_critical("مستوى بدون رقم مستوى (level_number/level)")
            continue
        level_numbers.append(level[LEVEL_NUMBER_KEY])

    report.level_count = len(set(level_numbers))

    missing_levels = [n for n in EXPECTED_LEVEL_NUMBERS if n not in level_numbers]
    if missing_levels:
        report.add_critical(f"مستويات ناقصة من 0 إلى 5: {missing_levels}")

    duplicate_levels = {n for n in level_numbers if level_numbers.count(n) > 1}
    if duplicate_levels:
        report.add_critical(f"أرقام مستويات مكررة: {sorted(duplicate_levels)}")


def _is_malformed_code(code: str) -> bool:
    return not VALID_CODE_PATTERN.match(code)


def _has_suspicious_text(text: str) -> bool:
    """Heuristic check for obviously garbled Arabic text (broken words)."""
    for token in SUSPICIOUS_TOKEN_PATTERN.findall(text):
        if token not in COMMON_SHORT_ARABIC_WORDS:
            return True
    return False


def _acceptance_criteria_text(acceptance_criteria: Any) -> str:
    """Flattens acceptance_criteria (string or list of strings) into plain text."""
    if isinstance(acceptance_criteria, list):
        return " ".join(str(item) for item in acceptance_criteria)
    return str(acceptance_criteria) if acceptance_criteria is not None else ""


def _check_levels_content(levels: list[dict[str, Any]], report: FileReport) -> None:
    all_codes: list[str] = []

    for level in levels:
        level_number = level.get(LEVEL_NUMBER_KEY, "?")
        level_name = level.get(LEVEL_NAME_KEY)

        if not level_name or not str(level_name).strip():
            report.add_critical(f"المستوى {level_number}: اسم المستوى (level_name) فارغ")

        if EVIDENCE_LIST_KEY not in level:
            report.add_critical(f"المستوى {level_number}: حقل الأدلة (evidence) غير موجود")
            continue

        evidence_items = level[EVIDENCE_LIST_KEY]
        report.evidence_count += len(evidence_items)

        for evidence in evidence_items:
            code = evidence.get(EVIDENCE_CODE_KEY)
            name = evidence.get(EVIDENCE_NAME_KEY)

            if not code or not str(code).strip():
                report.add_critical(f"المستوى {level_number}: دليل بدون كود (evidence_code)")
            else:
                all_codes.append(str(code).strip())
                if _is_malformed_code(str(code).strip()):
                    report.add_critical(
                        f"المستوى {level_number}: كود بصيغة خاطئة '{code}' "
                        f"(الصيغة المتوقعة مثل DC.C.{level_number}.1 أو DC.M.n)"
                    )

            if not name or not str(name).strip():
                report.add_critical(f"المستوى {level_number}: دليل بدون اسم (evidence_name), الكود: {code}")
            elif _has_suspicious_text(str(name)):
                report.add_warning(f"المستوى {level_number}: اسم الدليل يحتوي كلمات مشوهة محتملة: '{name}'")

            if EVIDENCE_ACCEPTANCE_CRITERIA_KEY not in evidence:
                report.add_warning(f"المستوى {level_number}: لا يوجد acceptance_criteria للدليل (الكود: {code})")
            else:
                acceptance_text = _acceptance_criteria_text(evidence[EVIDENCE_ACCEPTANCE_CRITERIA_KEY])
                if not acceptance_text.strip():
                    report.add_warning(f"المستوى {level_number}: acceptance_criteria فارغ, الكود: {code}")
                elif _has_suspicious_text(acceptance_text):
                    report.add_warning(
                        f"المستوى {level_number}: acceptance_criteria يحتوي كلمات مشوهة محتملة (الكود: {code})"
                    )

            if "related_specifications" not in evidence:
                report.add_warning(
                    f"المستوى {level_number}: لا يوجد related_specifications للدليل (الكود: {code})"
                )

    report.code_count = len(all_codes)

    duplicate_codes = sorted({code for code in all_codes if all_codes.count(code) > 1})
    if duplicate_codes:
        report.add_critical(f"أكواد مكررة داخل نفس MQ: {duplicate_codes}")


def _build_recommendations(report: FileReport) -> None:
    if any("الصيغة المتوقعة" in error for error in report.critical_errors):
        report.add_recommendation("تصحيح الأكواد المخالفة لتتبع الصيغة DC.C.<level>.<n> أو DC.M.<n>")
    if any("لا يوجد acceptance_criteria" in warning or "acceptance_criteria فارغ" in warning for warning in report.warnings):
        report.add_recommendation("مراجعة الأدلة التي لا يوجد بها acceptance_criteria أو محتواها فارغ")
    if any("related_specifications" in warning for warning in report.warnings):
        report.add_recommendation("تعبئة حقل related_specifications لكل دليل لدعم التتبع (traceability)")
    if any("مشوهة" in warning for warning in report.warnings):
        report.add_recommendation("مراجعة النصوص المرصودة كمحتملة التشوه يدوياً للتأكد من سلامتها")


def check_file(file_path: Path) -> FileReport:
    """Runs all quality checks on a single maturity model JSON file."""
    report = FileReport(file_path.name)

    data = _load_json_file(file_path)
    if data is None:
        report.add_critical("تعذرت قراءة الملف أو أن محتواه ليس JSON صالح")
        return report

    _check_top_level_fields(data, report)

    levels = data.get("levels")
    if isinstance(levels, list):
        _check_levels_coverage(levels, report)
        _check_levels_content(levels, report)
    else:
        report.add_critical("حقل levels مفقود أو ليس قائمة")

    _build_recommendations(report)
    return report


def _print_report(report: FileReport) -> None:
    print("=" * 70)
    print(f"اسم الملف        : {report.file_name}")
    print(f"عدد المستويات    : {report.level_count}/6")
    print(f"عدد الأدلة       : {report.evidence_count}")
    print(f"عدد الأكواد      : {report.code_count}")

    print(f"\nالأخطاء الحرجة ({len(report.critical_errors)}):")
    if report.critical_errors:
        for error in report.critical_errors:
            print(f"  - {error}")
    else:
        print("  لا توجد أخطاء حرجة")

    print(f"\nالتحذيرات ({len(report.warnings)}):")
    if report.warnings:
        for warning in report.warnings:
            print(f"  - {warning}")
    else:
        print("  لا توجد تحذيرات")

    print(f"\nالتوصيات ({len(report.recommendations)}):")
    for recommendation in report.recommendations:
        print(f"  - {recommendation}")
    print()


def main() -> None:
    """Checks all DC maturity model JSON files and prints a quality report."""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    project_root = Path(__file__).resolve().parents[2]
    maturity_models_dir = project_root / "data" / "maturity_models"

    reports = []
    for file_name in MATURITY_MODEL_FILE_NAMES:
        file_path = maturity_models_dir / file_name
        reports.append(check_file(file_path))

    print("تقرير فحص جودة ملفات نموذج النضج - مجال تصنيف البيانات (DC)")
    for report in reports:
        _print_report(report)

    total_critical = sum(len(r.critical_errors) for r in reports)
    total_warnings = sum(len(r.warnings) for r in reports)
    print("=" * 70)
    print("الملخص العام")
    print(f"عدد الملفات المفحوصة : {len(reports)}")
    print(f"إجمالي الأخطاء الحرجة : {total_critical}")
    print(f"إجمالي التحذيرات      : {total_warnings}")


if __name__ == "__main__":
    main()
