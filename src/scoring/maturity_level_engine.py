"""
Maturity Level Engine
======================

⚠️ تحذير معماري (من مراجعة معمارية لمنصة NDI-Sentinel — راجع قبل أي استخدام):

هذا الملف **غير مطابق حالياً** لمنهجية SDAIA/NDMO الموثّقة في صفحة 18 من
"المحتوى التدريبي لمؤشر نضيء" (المرجع المنهجي الوحيد المعتمد). أوجه عدم
التطابق موثّقة بدقة أدناه؛ لم يُعدَّل أي منطق حساب في هذا الملف ضمن هذه
المراجعة — فقط تصنيف/توثيق.

يحوّل هذا الملف حالياً compliance_percentage (الناتج من Domain Progress
Engine — src/scoring/domain_progress_engine.py، وتحديداً mq_progress) إلى
مستويات نضج (0 → 5) عبر نطاقات نسبية ثابتة (20% لكل مستوى، انظر
_percentage_to_level أدناه).

أوجه عدم التطابق مع صفحة 18/12/11 (موثّقة، لا اجتهاد):
  1. المُدخل: صفحة 18 تشترط إجابات مستوى نضج (0-5) مباشرة لكل معيار من
     الاستبيان. المُدخل الفعلي هنا (compliance_percentage) هو أصلاً ناتج
     تغطية نصية من src/evidence_assessment/gap_analysis_engine.py، ممرَّراً
     عبر domain_progress_engine.py — وليس إجابة نضج مباشرة.
  2. المعادلة: صفحة 18 تنص صراحة على
         D = Σ(وزن المجال × متوسط النتيجة لكل مجال)
     هذا الملف لا يطبّق هذه المعادلة إطلاقاً — يستخدم بدلاً منها نطاقات
     نسبية ثابتة (_percentage_to_level).
  3. الأوزان: صفحة 12 توفّر 14 وزناً صريحاً للمجالات (11.93%...3.16%).
     هذا الملف لا يستخدم أي مصفوفة أوزان إطلاقاً.
  4. الأسماء: صفحة 11 تُسمّي المستويات (غياب القدرات/البناء/التعريف/
     التفعيل/التمكن/الريادة). هذا الملف يستخدم أسماء مختلفة تماماً
     (Nonexistent/Initial/Managed/Defined/Quantitatively Managed/Optimized)
     غير موجودة في المصدر SDAIA المعتمد.
  5. الاستقلالية: صفحة 22 تشترط استقلال مصدري أدلة الامتثال والنضج عمداً.
     هذا الملف يعتمد كلياً على compliance_percentage كمُدخل وحيد — أي
     مخالفة مباشرة لهذا المبدأ إن استُخدم مع بيانات امتثال حقيقية مستقبلاً.

لا يُستدعى هذا الملف حالياً من dashboard/data_layer.py (current_level يبقى
فارغاً هناك عمداً) — أي أن هذا الاعتماد المخالف موجود بنيوياً في الكود لكنه
غير مُفعَّل في مسار العرض الحالي. عند بناء Maturity Calculation Layer
حقيقية مستقبلاً، يجب أن تُبنى من الصفر وفق صفحة 18 مباشرة، وليس بتعديل هذا
الملف تدريجياً.

Pure Python فقط. لا يستخدم أي LLM أو OCR أو قاعدة بيانات أو أي خدمة خارجية.

---
تحديث (إصلاح معماري لاحق — حماية مدخلات فقط، لا تغيير في المعادلة):

الدوال calculate_mq_maturity() و calculate_domain_maturity() هي بالضبط
المسار المخالف الموصوف أعلاه (تمرّر compliance_percentage/
evidence_coverage_percentage من mq_progress — وهو مخرج تغطية أدلة نصية
داخلية من domain_progress_engine.py — مباشرة إلى calculate_maturity_level).
أصبحتا الآن ترفضان العمل فوراً وتُطلقان MaturityInputGuardError، بدل حساب
نتيجة قد تُقرأ خطأً كنضج SDAIA رسمي. calculate_maturity_level() نفسها لم
تتغير في المعادلة أو النطاقات (فقط اسم المعامل)، وتبقى قابلة للاستخدام
المباشر عندما يُمرَّر لها مستوى نضج فعلي (0-5) مُشتق بشكل صحيح مستقبلاً وفق
صفحة 18 — لا يوجد أي مسار في هذا الملف يفعل ذلك حالياً.
"""

from __future__ import annotations

from typing import Any, Dict, List

MATURITY_LEVEL_NAMES = {
    0: "Nonexistent",
    1: "Initial",
    2: "Managed",
    3: "Defined",
    4: "Quantitatively Managed",
    5: "Optimized",
}

MATURITY_LEVEL_NAMES_AR = {
    0: "غير موجود",
    1: "ابتدائي",
    2: "مدار",
    3: "معرف",
    4: "مُدار كمياً",
    5: "محسن",
}


class MaturityInputGuardError(Exception):
    """يُطلَق عند محاولة تمرير مخرجات Evidence Coverage (من
    domain_progress_engine.py، عبر mq_progress/mq_progress_item) كمدخل
    مباشر لحساب مستوى نضج SDAIA رسمي.

    هذا ليس خطأ تشغيلياً عرضياً — هذا حماية معمارية مقصودة: Evidence
    Coverage ≠ Maturity. راجع التحذير المعماري في أعلى هذا الملف لتفاصيل
    أوجه عدم التطابق مع صفحة 18 من مصدر نضيء.
    """


def _percentage_to_level(evidence_coverage_percentage: float) -> int:
    if evidence_coverage_percentage <= 0:
        return 0
    if evidence_coverage_percentage <= 20:
        return 1
    if evidence_coverage_percentage <= 40:
        return 2
    if evidence_coverage_percentage <= 60:
        return 3
    if evidence_coverage_percentage <= 80:
        return 4
    return 5


def calculate_maturity_level(evidence_coverage_percentage: float) -> Dict[str, Any]:
    """يحول نسبة (0-100) إلى مستوى نضج (0-5) مع الاسم الإنجليزي والعربي، عبر نطاقات
    ثابتة (_percentage_to_level) — وليس معادلة صفحة 18 الرسمية (D = Σ(وزن المجال ×
    متوسط النتيجة)). اسم المعامل لا يعني أن هذه الدالة "رسمية" SDAIA؛ فقط أنها لا
    تفترض مصدر القيمة. الاستدعاء المباشر من مصدر Evidence Coverage محظور عبر
    calculate_mq_maturity/calculate_domain_maturity أدناه (انظر MaturityInputGuardError)."""
    level = _percentage_to_level(evidence_coverage_percentage)
    return {
        "maturity_level": level,
        "maturity_level_name": MATURITY_LEVEL_NAMES[level],
        "maturity_level_name_ar": MATURITY_LEVEL_NAMES_AR[level],
    }


def calculate_mq_maturity(mq_progress_item: Dict[str, Any]) -> Dict[str, Any]:
    """محظورة عمداً — انظر MaturityInputGuardError.

    مدخلها الطبيعي (mq_progress_item من domain_progress_engine.py) يحمل
    compliance_percentage/evidence_coverage_percentage، وهو مخرج تغطية أدلة
    نصية داخلي وليس إجابة نضج (0-5) مباشرة كما تشترط صفحة 18. تمريره إلى
    calculate_maturity_level() هو بالضبط الخلط الممنوع بين Evidence Coverage
    و Maturity.

    Raises:
        MaturityInputGuardError: دائماً.
    """
    raise MaturityInputGuardError(
        "calculate_mq_maturity() blocked: its input (mq_progress_item from "
        "domain_progress_engine.py) carries an internal evidence-coverage "
        "percentage, not an official SDAIA maturity level (0-5) per page 18 "
        "of the نضيء source. Feeding it into calculate_maturity_level() "
        "would conflate Evidence Coverage with Maturity. Requires Human "
        "Decision / an official SDAIA/NDMO-defined conversion rule before "
        "this function can be implemented."
    )


def calculate_domain_maturity(mq_progress: List[Dict[str, Any]]) -> Dict[str, Any]:
    """محظورة عمداً — انظر MaturityInputGuardError.

    نفس سبب حظر calculate_mq_maturity(): مدخلها (mq_progress) مبني من
    نسب تغطية أدلة نصية داخلية، وليس إجابات نضج رسمية مستقلة كما تشترط
    صفحة 22 (استقلال مصدري أدلة الامتثال والنضج).

    Raises:
        MaturityInputGuardError: دائماً.
    """
    raise MaturityInputGuardError(
        "calculate_domain_maturity() blocked: mq_progress is built from "
        "internal evidence-coverage percentages (domain_progress_engine.py), "
        "not independent official SDAIA maturity answers per page 18/22 of "
        "the نضيء source. Requires Human Decision / an official SDAIA/NDMO-"
        "defined conversion rule before this function can be implemented."
    )


def main() -> None:
    test_cases = [
        (0, 0),
        (10, 1),
        (30, 2),
        (50, 3),
        (70, 4),
        (95, 5),
    ]

    passed = 0
    failed = 0

    print("=" * 60)
    print("اختبارات calculate_maturity_level")
    print("=" * 60)

    for evidence_coverage_percentage, expected_level in test_cases:
        result = calculate_maturity_level(evidence_coverage_percentage)
        actual_level = result["maturity_level"]
        is_pass = actual_level == expected_level

        if is_pass:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        print(
            f"[{status}] input={evidence_coverage_percentage}% -> "
            f"maturity_level={actual_level} "
            f"({result['maturity_level_name']} / {result['maturity_level_name_ar']}) "
            f"[expected={expected_level}]"
        )

    print()
    print("=" * 60)
    print("اختبار الحماية: استدعاء calculate_domain_maturity() بمدخل mq_progress")
    print("(evidence-coverage) يجب أن يُطلق MaturityInputGuardError دائماً")
    print("=" * 60)

    sample_mq_progress = [
        {"mq_id": "DC.MQ.1", "compliance_percentage": 100},
        {"mq_id": "DC.MQ.2", "compliance_percentage": 50},
        {"mq_id": "DC.MQ.3", "compliance_percentage": 0},
    ]

    try:
        calculate_domain_maturity(sample_mq_progress)
        guard_passed = False
        print("[FAIL] لم يتم إطلاق MaturityInputGuardError كما هو متوقع")
    except MaturityInputGuardError as exc:
        guard_passed = True
        print(f"[PASS] MaturityInputGuardError: {exc}")

    if guard_passed:
        passed += 1
    else:
        failed += 1

    print()
    print("=" * 60)
    print(f"عدد الاختبارات الناجحة: {passed}")
    print(f"عدد الاختبارات الفاشلة: {failed}")
    overall_result = "PASS" if failed == 0 else "FAIL"
    print(f"Overall Result: {overall_result}")
    print("=" * 60)


if __name__ == "__main__":
    main()
