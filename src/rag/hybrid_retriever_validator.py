"""
Hybrid Retriever Validator — التحقق من دقة hybrid_retriever.py قبل ربطه بأي LLM.

لا يُستخدم LLM ولا LangChain ولا AI Agent — فحوصات مباشرة على مخرجات
hybrid_search() مقابل النتائج المتوقعة.

المصدر: src/rag/hybrid_retriever.py (قراءة فقط عبر الاستدعاء)
الناتج: reports/hybrid_retriever_validation_report.txt (UTF-8)
"""

import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.hybrid_retriever import hybrid_search  # noqa: E402

REPORT_PATH = PROJECT_ROOT / "reports" / "hybrid_retriever_validation_report.txt"

TEST_CASES = [
    {
        "id": 1,
        "query": "سياسة تصنيف البيانات",
        "expected": {"detected_evidence_code": "DC.M.6"},
    },
    {
        "id": 2,
        "query": "سجل البيانات",
        "expected": {"detected_evidence_code": "DC.C.5.1"},
    },
    {
        "id": 3,
        "query": "أداة أتمتة تصنيف البيانات",
        "expected": {"detected_evidence_code": "DC.M.9"},
    },
    {
        "id": 4,
        "query": "ما المطلوب في DC.M.6؟",
        "expected": {"strategy": "evidence_code", "detected_evidence_code": "DC.M.6"},
    },
    {
        "id": 5,
        "query": "ما المطلوب لتعريف تصنيف البيانات؟",
        "expected": {"strategy": "semantic_only"},
    },
]


class ValidationResult:
    def __init__(self, test_id, query, expected):
        self.test_id = test_id
        self.query = query
        self.expected = expected
        self.status = "PASS"
        self.details = []
        self.warnings = []

    def fail(self, message):
        self.status = "FAIL"
        self.details.append(message)

    def ok(self, message):
        self.details.append(message)

    def warn(self, message):
        self.warnings.append(message)


def run_test_case(case):
    r = ValidationResult(case["id"], case["query"], case["expected"])

    try:
        results = hybrid_search(case["query"], top_k=5)
    except Exception as exc:
        r.fail(f"استدعاء hybrid_search فشل: {exc}")
        return r

    if not results:
        r.warn("لم تُعَد أي نتائج من hybrid_search — تعذر التحقق من الحقول المتوقعة.")
        r.fail("لا توجد نتيجة أولى للتحقق منها.")
        return r

    top = results[0]

    for field, expected_value in case["expected"].items():
        actual_value = top.get(field)
        if actual_value == expected_value:
            r.ok(f"{field} = {actual_value} (متوقع: {expected_value})")
        else:
            r.fail(f"{field} = {actual_value} (متوقع: {expected_value})")

    r.ok(
        f"أفضل نتيجة: evidence_code={top.get('evidence_code')} | "
        f"source_document={top.get('source_document')} | page_number={top.get('page_number')}"
    )

    return r


def build_report_text(results):
    lines = []
    lines.append("=" * 60)
    lines.append("تقرير التحقق من Hybrid Retriever")
    lines.append("Hybrid Retriever Validation Report")
    lines.append("=" * 60)
    lines.append("")

    pass_count = sum(1 for r in results if r.status == "PASS")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    warnings_count = sum(len(r.warnings) for r in results)
    overall_result = "FAIL" if fail_count > 0 else "PASS"

    lines.append(f"عدد الاختبارات: {len(results)}")
    lines.append(f"عدد PASS: {pass_count}")
    lines.append(f"عدد FAIL: {fail_count}")
    lines.append(f"عدد Warnings: {warnings_count}")
    lines.append(f"النتيجة النهائية: {overall_result}")
    lines.append("")
    lines.append("=" * 60)

    for r in results:
        lines.append("")
        lines.append("-" * 60)
        lines.append(f"اختبار {r.test_id}: \"{r.query}\"")
        lines.append(f"الحالة: [{r.status}]")
        lines.append("-" * 60)
        for detail in r.details:
            lines.append(f"  - {detail}")
        for warning in r.warnings:
            lines.append(f"  [WARNING] {warning}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines), pass_count, fail_count, warnings_count, overall_result


def main():
    results = [run_test_case(case) for case in TEST_CASES]

    report_text, pass_count, fail_count, warnings_count, overall_result = build_report_text(results)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"عدد PASS: {pass_count}")
    print(f"عدد FAIL: {fail_count}")
    print(f"عدد Warnings: {warnings_count}")
    print(f"Overall Result: {overall_result}")


if __name__ == "__main__":
    main()
