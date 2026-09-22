"""
Response Parser — يحوّل مخرجات LLM الخام (نص JSON متوقع) إلى بنية ثابتة
موحّدة، جاهزة للاستخدام لاحقاً في Word Generator وPowerPoint Generator
والـ Dashboard وتقارير الامتثال.

لا يُستدعى أي LLM هنا ولا أي API خارجي — فقط parsing وتطبيع نصي/بنيوي
(JSON parsing + dict normalization) بدون أي منطق شبكي.
"""

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_STRUCTURE = {
    "executive_summary": "",
    "compliance_analysis": "",
    "required_evidence": [],
    "references": [],
    "confidence": "",
    "limitations": "",
    "follow_up_questions": [],
}

REQUIRED_KEYS = list(DEFAULT_STRUCTURE.keys())
LIST_KEYS = ["required_evidence", "references", "follow_up_questions"]

MOCK_RESPONSE_TEXT = json.dumps(
    {
        "executive_summary": "الجهة لم تُوفر بعد وثيقة سياسة تصنيف بيانات معتمدة رسمياً.",
        "compliance_analysis": (
            "بناءً على السياق المسترجع، يتطلب الدليل DC.M.6 إرفاق سياسة معتمدة "
            "من صاحب الصلاحية تشمل اسم السياسة وتاريخ الإصدار ورقم الإصدار كحد أدنى."
        ),
        "required_evidence": [
            "سياسة تصنيف بيانات معتمدة من صاحب الصلاحية",
            "تحديد اسم السياسة وتاريخ ورقم الإصدار",
        ],
        "references": [
            {"evidence_code": "DC.M.6", "source_document": "سياسة تصنيف البيانات", "page_number": 2},
            {"evidence_code": "DC.M.6", "source_document": "المؤشر الوطني للبيانات", "page_number": 210},
        ],
        "confidence": "عالية",
        "limitations": "الإجابة تعتمد فقط على المقاطع المسترجعة ولا تغطي كل تفاصيل الوثيقة الكاملة.",
        "follow_up_questions": [
            "هل تم اعتماد السياسة من صاحب الصلاحية رسمياً؟",
            "هل توجد آلية مراجعة دورية لسياسة التصنيف؟",
        ],
    },
    ensure_ascii=False,
)


def _default_structure():
    return {
        "executive_summary": "",
        "compliance_analysis": "",
        "required_evidence": [],
        "references": [],
        "confidence": "",
        "limitations": "",
        "follow_up_questions": [],
    }


def _coerce_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def normalize_response(parsed_response):
    """يضمن وجود كل المفاتيح الرسمية، ويحوّل حقول القوائم إلى list دائماً."""
    if not isinstance(parsed_response, dict):
        parsed_response = {}

    normalized = _default_structure()
    for key in REQUIRED_KEYS:
        if key in parsed_response:
            normalized[key] = parsed_response[key]

    for key in LIST_KEYS:
        normalized[key] = _coerce_list(normalized[key])

    return normalized


def parse_response(response_text):
    """يقرأ response_text كـ JSON إن أمكن، ثم يطبّعه إلى البنية الرسمية.

    لا يرمي أي Exception بأي حال — أي فشل في القراءة يُعيد بنية فارغة
    بالقيم الافتراضية.
    """
    try:
        parsed = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        return _default_structure()

    if not isinstance(parsed, dict):
        return _default_structure()

    return normalize_response(parsed)


def validate_response_structure(parsed_response):
    """يتحقق من اكتمال البنية الرسمية دون رمي أي Exception.

    يعيد (is_valid: bool, issues: list[str]) حيث تحتوي issues على أسماء
    المفاتيح الناقصة، بالإضافة إلى أي حقل قائمة (required_evidence/
    references/follow_up_questions) موجود لكن ليس من نوع list.
    """
    issues = []

    if not isinstance(parsed_response, dict):
        return False, ["parsed_response ليس من نوع dict"]

    for key in REQUIRED_KEYS:
        if key not in parsed_response:
            issues.append(key)

    for key in LIST_KEYS:
        if key in parsed_response and not isinstance(parsed_response[key], list):
            issues.append(f"{key} (موجود لكنه ليس list)")

    return len(issues) == 0, issues


def _print_demo_result(mock_response_text):
    parsing_succeeded = True
    try:
        parsed = parse_response(mock_response_text)
    except Exception:
        parsing_succeeded = False
        parsed = _default_structure()

    is_valid, issues = validate_response_structure(parsed)

    print(f"هل Parsing نجح؟ {'نعم' if parsing_succeeded else 'لا'}")
    print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"  المفاتيح/المشاكل الناقصة: {issues}")
    print(f"عدد المفاتيح النهائية: {len(parsed)}")
    print(f"أسماء المفاتيح النهائية: {list(parsed.keys())}")
    print(f"مثال executive_summary: {parsed['executive_summary']}")


def main():
    print("=" * 60)
    print("تجربة 1: Mock Response صالح (JSON كامل)")
    print("=" * 60)
    _print_demo_result(MOCK_RESPONSE_TEXT)

    print("\n" + "=" * 60)
    print("تجربة 2: نص غير صالح كـ JSON (Fallback)")
    print("=" * 60)
    _print_demo_result("هذا نص عادي وليس JSON صالح")


if __name__ == "__main__":
    main()
