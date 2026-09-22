"""
Evidence Text Assessment Engine (V3) — يقارن نص دليل مُقدَّم فعلياً بقواعد التقييم
الداخلية لكود دليل معيّن (مصدرها data/rules/compliance_rules.json)، ويصدر حالة
تقييم نصي داخلية (PASS / PARTIAL_PASS / FAIL / NOT_PROVIDED).

توصيف معماري مهم (راجع تقرير المراجعة المعمارية لمنصة NDI-Sentinel):
الحالة الناتجة من هذا الملف (`overall_status` وما يُبنى عليها لاحقاً مثل
`coverage_percentage`) هي **Internal Evidence Assessment Status** —
نتاج تحليل نص داخلي بعتبات مصممة هندسياً (COVERAGE_PASS_THRESHOLD=90،
COVERAGE_PARTIAL_THRESHOLD=60 أدناه)، وليست **SDAIA Compliance Result**
الرسمي. منهجية SDAIA/NDMO (صفحة 14 من "المحتوى التدريبي لمؤشر نضيء")
تُعرِّف الامتثال كتسجيل ثنائي (0% / 100%) على مستوى المواصفة (191 مواصفة)،
وليس كتسجيل نصي مستمر رباعي الحالات على مستوى الدليل الواحد كما هنا.
لا يجوز اعتبار مخرجات هذا الملف بديلاً عن Compliance Decision Layer
(انظر src/compliance/compliance_decision_layer.py) عند بنائها.

هذا الملف لا يزال يؤدي وظيفته الأصلية (تحليل تغطية نصية للدليل) بلا أي
تغيير في المنطق أو العتبات — هذا التوصيف تصنيفي/توثيقي فقط.

لا يُستخدم أي LLM ولا LangChain ولا أي API خارجي هنا — فقط قواعد نصية ثابتة
(Keyword Matching بسيط) فوق أربعة ملفات بيانات محلية جاهزة:

1. data/rules/compliance_rules.json           (المصدر الأساسي لقواعد التقييم)
2. data/knowledge_graph/dc_knowledge_graph.json (اسم الدليل والمراجع + fallback)
3. data/rag_index/dc_rag_metadata_index.json    (fallback فقط عند غياب rule)
4. data/rag_index/dc_rag_content_index.json     (fallback فقط عند غياب rule)

منطق التقييم (بلا تغيير):

- Mandatory Gate: يعتمد على required_terms المخزّنة في الـ rule (وليس أول
  Acceptance Criteria كما في النسخ السابقة). يجب أن تتحقق كل required_terms
  نصياً في الدليل المقدَّم وإلا overall_status = FAIL.
- Acceptance Criteria Audit: تدقيق مستقل لكل بند من critical_criteria و
  medium_criteria المخزّنة في الـ rule (PASS/FAIL + matched/missing terms).
- Coverage: تُحسب فقط من critical_criteria + medium_criteria.
- إذا لم يوجد rule لدليل معيّن ضمن compliance_rules.json، يُستخدم fallback آمن
  (أول Acceptance Criteria من Knowledge Graph كـ Mandatory كما في السابق) مع
  تعيين warning داخل النتيجة وneeds_human_review=True.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

RULES_PATH = PROJECT_ROOT / "data" / "rules" / "compliance_rules.json"
KNOWLEDGE_GRAPH_PATH = (
    PROJECT_ROOT / "data" / "knowledge_graph" / "dc_knowledge_graph.json"
)
METADATA_INDEX_PATH = (
    PROJECT_ROOT / "data" / "rag_index" / "dc_rag_metadata_index.json"
)
CONTENT_INDEX_PATH = (
    PROJECT_ROOT / "data" / "rag_index" / "dc_rag_content_index.json"
)

CONTENT_FALLBACK_CHUNK_TYPES = {
    "detailed_requirement_content",
    "official_reference_content",
    "supporting_policy_content",
}

STOPWORDS = {
    "يجب", "على", "الجهة", "إرفاق", "أن", "تشمل", "كحد", "أدنى", "ما", "يلي",
    "من", "في", "إلى", "عن", "و", "أو", "مع", "التي", "الذي", "هل", "هو",
    "هي", "كل", "عند", "هذا", "هذه", "ذلك", "دون", "غير", "أي", "لا", "لم",
    "قد", "بين", "بها", "به", "لها", "له",
}

# عتبات هندسية داخلية لتصنيف Internal Evidence Assessment Status — غير مأخوذة
# من أي صفحة في مصدر SDAIA/NDMO (صفحات 8-23)، ولا يجوز اعتبارها Threshold
# رسمياً لـ SDAIA Compliance. القيم لم تُغيَّر ضمن هذه المراجعة المعمارية.

COVERAGE_PASS_THRESHOLD = 90
COVERAGE_PARTIAL_THRESHOLD = 60

_sources_cache = None


def _normalize(text):
    if not text:
        return ""
    return unicodedata.normalize("NFC", text).strip()


def _tokenize(text):
    text = re.sub(r"""[؟?.,:;!"'()،ـ\n]""", " ", text)
    return [t for t in text.split() if t]


def _keywords(text):
    return [
        t
        for t in _tokenize(_normalize(text))
        if t not in STOPWORDS and len(t) >= 2
    ]


def _keyword_found(keyword, text_raw, text_tokens):
    if keyword in text_raw:
        return True

    for token in text_tokens:
        if len(token) < 3:
            continue
        if keyword in token or token in keyword:
            return True

    return False


def _split_acceptance_text(text):
    if not text:
        return []

    parts = re.split(r"[\n]+|(?<=[.:])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_sources():
    """يحمّل ملفات القواعد ومصادر الـ fallback مرة واحدة فقط ويبني فهارس جاهزة."""
    global _sources_cache

    if _sources_cache is not None:
        return _sources_cache

    rules_by_code = _load_json(RULES_PATH) if RULES_PATH.exists() else {}

    kg_data = _load_json(KNOWLEDGE_GRAPH_PATH)
    kg_by_code = {
        node["evidence_code"]: node
        for node in kg_data.get("nodes", [])
    }

    metadata_acceptance_by_code = {}

    for chunk in _load_json(METADATA_INDEX_PATH):
        if chunk.get("chunk_type") == "acceptance_criteria":
            code = chunk["evidence_code"]
            existing = metadata_acceptance_by_code.get(code, "")
            metadata_acceptance_by_code[code] = (
                existing + "\n" + chunk["text"]
            ).strip()

    content_fallback_by_code = {}

    for chunk in _load_json(CONTENT_INDEX_PATH):
        if chunk.get("chunk_type") in CONTENT_FALLBACK_CHUNK_TYPES:
            code = chunk["evidence_code"]
            existing = content_fallback_by_code.get(code, "")
            content_fallback_by_code[code] = (
                existing + "\n" + chunk["text"]
            ).strip()

    _sources_cache = {
        "rules_by_code": rules_by_code,
        "kg_by_code": kg_by_code,
        "metadata_acceptance_by_code": metadata_acceptance_by_code,
        "content_fallback_by_code": content_fallback_by_code,
    }

    return _sources_cache


def _resolve_acceptance_criteria(node, evidence_code, sources):
    acceptance_criteria = node.get("acceptance_criteria") or []

    if acceptance_criteria:
        return acceptance_criteria

    fallback = _split_acceptance_text(
        sources["metadata_acceptance_by_code"].get(evidence_code, "")
    )

    if fallback:
        return fallback

    return _split_acceptance_text(
        sources["content_fallback_by_code"].get(evidence_code, "")
    )


def _fallback_rule(evidence_code, node, sources):
    """Rule آمن بديل عند غياب evidence_code من compliance_rules.json — يعيد
    استخدام أول Acceptance Criteria كـ Mandatory كما في المنطق القديم."""
    acceptance_criteria = _resolve_acceptance_criteria(
        node, evidence_code, sources
    )

    if not acceptance_criteria:
        return {
            "document_type": "Other",
            "mandatory_requirement": None,
            "required_terms": [],
            "critical_criteria": [],
            "medium_criteria": [],
            "confidence": "low",
            "needs_human_review": True,
        }

    mandatory_text = acceptance_criteria[0]

    return {
        "document_type": "Other",
        "mandatory_requirement": mandatory_text,
        "required_terms": _keywords(mandatory_text),
        "critical_criteria": [],
        "medium_criteria": list(acceptance_criteria[1:]),
        "confidence": "low",
        "needs_human_review": True,
    }


def _get_mandatory_text(rule):
    mandatory = rule.get("mandatory_requirement")

    if isinstance(mandatory, dict):
        return mandatory.get("description") or mandatory.get("text")

    return mandatory


def _get_required_terms(rule):
    mandatory = rule.get("mandatory_requirement")

    if isinstance(mandatory, dict):
        terms = mandatory.get("required_terms")

        if terms:
            return terms

    return rule.get("required_terms") or []


def _check_mandatory_gate(required_terms, provided_text_raw):
    """
    يتحقق من وجود كل required_terms مع تطبيع بسيط للاختلافات العربية،
    مثل:
        تحسين مستمر
    مقابل:
        التحسين المستمر

    لا يغيّر required_terms نفسها، وإنما يطبّعها فقط أثناء المقارنة.
    """
    if not required_terms:
        return False, [], []

    def normalize_term(text):
        text = _normalize(text)

        # إزالة "الـ" من بداية الكلمات حتى تتطابق:
        # تحسين ↔ التحسين
        text = re.sub(r"\bال", "", text)

        # توحيد المسافات
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    normalized_text = normalize_term(provided_text_raw)

    matched = []
    missing = []

    for term in required_terms:
        normalized_term = normalize_term(term)

        if normalized_term in normalized_text:
            matched.append(term)
        else:
            missing.append(term)

    return len(missing) == 0, matched, missing


def _is_item_satisfied(item_text, provided_text_raw, provided_tokens):
    """يقيّم بند Critical/Medium واحداً ويعيد
    (satisfied, matched_terms, missing_terms)."""
    item_keywords = _keywords(item_text)

    if not item_keywords:
        return False, [], []

    matched = [
        k
        for k in item_keywords
        if _keyword_found(k, provided_text_raw, provided_tokens)
    ]

    missing = [k for k in item_keywords if k not in matched]
    ratio = len(matched) / len(item_keywords)

    keyword_count = len(item_keywords)

    if keyword_count <= 2:
        required_ratio = 1.0
    elif keyword_count <= 5:
        required_ratio = 0.8
    else:
        required_ratio = 0.7

    satisfied = ratio >= required_ratio

    return satisfied, matched, missing


def _build_recommendation_note(
    overall_status,
    evidence_name,
    evidence_code,
    mandatory_requirement_passed,
    critical_missing,
    medium_missing,
):
    label = (
        f"{evidence_name} ({evidence_code})"
        if evidence_name
        else evidence_code
    )

    if overall_status == "NOT_PROVIDED":
        return (
            f"الدليل '{label}' غير مقدَّم إطلاقاً. "
            f"يجب إرفاقه لإثبات الامتثال."
        )

    if not mandatory_requirement_passed:
        return (
            f"الدليل '{label}' لم يحقق المتطلب الإلزامي (Mandatory Gate) "
            f"بالكامل، لذلك يُعتبر الدليل غير ناجح (FAIL) بغض النظر عن "
            f"نسبة التغطية الإجمالية."
        )

    if overall_status == "PASS":
        return (
            f"النص المقدم لـ '{label}' يغطي متطلبات القبول بشكل كافٍ "
            f"(Coverage ممتازة)."
        )

    if overall_status == "PARTIAL_PASS":
        return (
            f"النص المقدم لـ '{label}' يغطي جزءاً من متطلبات القبول فقط. "
            f"يجب استكمال {len(medium_missing)} بند/بنود موضحة في "
            f"medium_missing."
        )

    return (
        f"النص المقدم لـ '{label}' لا يغطي متطلبات القبول الأساسية بشكل كافٍ. "
        f"يوصى بإعادة صياغة الدليل ليشمل البنود الناقصة "
        f"({len(critical_missing)} حرجة و{len(medium_missing)} متوسطة)."
    )


def _unknown_evidence_result(evidence_code):
    return {
        "evidence_code": evidence_code,
        "evidence_name": None,
        "document_type": None,
        "mandatory_requirement": None,
        "mandatory_requirement_passed": False,
        "overall_status": "FAIL",
        "coverage_percentage": 0,
        "total_criteria": 0,
        "passed_criteria": 0,
        "failed_criteria": 0,
        "criteria_results": [],
        "critical_missing": [],
        "medium_missing": [],
        "needs_human_review": True,
        "confidence": None,
        "references": [],
        "recommendation_note": (
            f"لم يتم العثور على الدليل '{evidence_code}' ضمن Knowledge Graph."
        ),
        "warning": (
            f"لا يوجد الدليل '{evidence_code}' لا في compliance_rules.json "
            f"ولا في Knowledge Graph."
        ),
    }


def analyze_gap(evidence_code, provided_evidence_text=""):
    """يدقق دليلاً معيّناً مقابل rule الخاص به في
    compliance_rules.json ويعيد تقرير امتثال كامل."""
    sources = _get_sources()

    node = sources["kg_by_code"].get(evidence_code)
    rule = sources["rules_by_code"].get(evidence_code)

    warning = None

    if rule is None:
        if node is None:
            return _unknown_evidence_result(evidence_code)

        rule = _fallback_rule(evidence_code, node, sources)

        warning = (
            f"لا يوجد rule للدليل '{evidence_code}' ضمن compliance_rules.json؛ "
            f"تم استخدام fallback آمن من acceptance_criteria الأصلية "
            f"(أول بند = Mandatory)."
        )

    evidence_name = node.get("evidence_name") if node else None
    references = (node.get("references") or []) if node else []

    document_type = rule.get("document_type")
    mandatory_requirement_text = _get_mandatory_text(rule)
    required_terms = _get_required_terms(rule)
    critical_criteria = rule.get("critical_criteria") or []
    medium_criteria = rule.get("medium_criteria") or []
    confidence = rule.get("confidence")
    needs_human_review = bool(
        rule.get("needs_human_review", False)
    )

    total_criteria = len(critical_criteria) + len(medium_criteria)

    provided_text_raw = _normalize(provided_evidence_text)

    if not provided_text_raw:
        criteria_results = [
            {
                "criterion": item,
                "status": "FAIL",
                "matched_terms": [],
                "missing_terms": _keywords(item),
            }
            for item in (critical_criteria + medium_criteria)
        ]

        critical_missing = list(critical_criteria)
        medium_missing = list(medium_criteria)

        result = {
            "evidence_code": evidence_code,
            "evidence_name": evidence_name,
            "document_type": document_type,
            "mandatory_requirement": mandatory_requirement_text,
            "mandatory_requirement_passed": False,
            "overall_status": "NOT_PROVIDED",
            "coverage_percentage": 0,
            "total_criteria": total_criteria,
            "passed_criteria": 0,
            "failed_criteria": total_criteria,
            "criteria_results": criteria_results,
            "critical_missing": critical_missing,
            "medium_missing": medium_missing,
            "needs_human_review": needs_human_review,
            "confidence": confidence,
            "references": references,
            "recommendation_note": _build_recommendation_note(
                "NOT_PROVIDED",
                evidence_name,
                evidence_code,
                False,
                critical_missing,
                medium_missing,
            ),
        }

        if warning:
            result["warning"] = warning

        return result

    provided_tokens = set(_tokenize(provided_text_raw))

    mandatory_requirement_passed, _mandatory_matched, _mandatory_missing = (
        _check_mandatory_gate(
            required_terms,
            provided_text_raw,
        )
    )

    criteria_results = []
    critical_missing = []
    medium_missing = []
    passed_criteria = 0

    for item in critical_criteria:
        satisfied, matched, missing = _is_item_satisfied(
            item,
            provided_text_raw,
            provided_tokens,
        )

        criteria_results.append(
            {
                "criterion": item,
                "status": "PASS" if satisfied else "FAIL",
                "matched_terms": matched,
                "missing_terms": missing,
            }
        )

        if satisfied:
            passed_criteria += 1
        else:
            critical_missing.append(item)

    for item in medium_criteria:
        satisfied, matched, missing = _is_item_satisfied(
            item,
            provided_text_raw,
            provided_tokens,
        )

        criteria_results.append(
            {
                "criterion": item,
                "status": "PASS" if satisfied else "FAIL",
                "matched_terms": matched,
                "missing_terms": missing,
            }
        )

        if satisfied:
            passed_criteria += 1
        else:
            medium_missing.append(item)

    failed_criteria = total_criteria - passed_criteria

    coverage_percentage = (
        round((passed_criteria / total_criteria) * 100)
        if total_criteria
        else 100
    )

    critical_failed = bool(critical_missing)

    if not mandatory_requirement_passed:
        overall_status = "FAIL"
    elif critical_failed:
        overall_status = "FAIL"
    elif coverage_percentage >= COVERAGE_PASS_THRESHOLD:
        overall_status = "PASS"
    elif coverage_percentage >= COVERAGE_PARTIAL_THRESHOLD:
        overall_status = "PARTIAL_PASS"
    else:
        overall_status = "FAIL"

    result = {
        "evidence_code": evidence_code,
        "evidence_name": evidence_name,
        "document_type": document_type,
        "mandatory_requirement": mandatory_requirement_text,
        "mandatory_requirement_passed": mandatory_requirement_passed,
        "overall_status": overall_status,
        "coverage_percentage": coverage_percentage,
        "total_criteria": total_criteria,
        "passed_criteria": passed_criteria,
        "failed_criteria": failed_criteria,
        "criteria_results": criteria_results,
        "critical_missing": critical_missing,
        "medium_missing": medium_missing,
        "needs_human_review": needs_human_review,
        "confidence": confidence,
        "references": references,
        "recommendation_note": _build_recommendation_note(
            overall_status,
            evidence_name,
            evidence_code,
            mandatory_requirement_passed,
            critical_missing,
            medium_missing,
        ),
    }

    if warning:
        result["warning"] = warning

    return result


def analyze_multiple(evidence_codes, provided_evidence_map):
    """يشغّل analyze_gap على قائمة أكواد أدلة، باستخدام
    provided_evidence_map (dict: evidence_code -> نص الدليل المقدَّم)
    لكل كود."""
    provided_evidence_map = provided_evidence_map or {}

    return [
        analyze_gap(code, provided_evidence_map.get(code, ""))
        for code in evidence_codes
    ]


def _print_result(result):
    print(f"\nevidence_code: {result['evidence_code']}")
    print("-" * 60)
    print(f"  document_type: {result['document_type']}")

    mandatory_label = (
        "PASS"
        if result["mandatory_requirement_passed"]
        else "FAIL"
    )

    print(
        f"  mandatory_requirement_passed: {mandatory_label}"
    )

    print(
        f"  coverage_percentage: "
        f"{result['coverage_percentage']}%"
    )

    print(
        f"  passed_criteria: "
        f"{result['passed_criteria']}/{result['total_criteria']}"
    )

    print(
        f"  failed_criteria: "
        f"{result['failed_criteria']}/{result['total_criteria']}"
    )

    print(
        f"  overall_status: "
        f"{result['overall_status']}"
    )

    print(
        f"  critical_missing "
        f"({len(result['critical_missing'])}):"
    )

    for item in result["critical_missing"]:
        print(f"    - {item}")

    print(
        f"  medium_missing "
        f"({len(result['medium_missing'])}):"
    )

    for item in result["medium_missing"]:
        print(f"    - {item}")

    print(
        f"  needs_human_review: "
        f"{result['needs_human_review']}"
    )

    if result.get("warning"):
        print(
            f"  [WARNING] "
            f"{result['warning']}"
        )


def main():
    warnings_and_errors = []
    successful = 0

    demo_cases = [
        ("DC.M.6", ""),
        (
            "DC.M.6",
            "سياسة تصنيف البيانات المعتمدة من صاحب الصلاحية وتشمل تاريخ الإصدار "
            "ونطاق السياسة وأدوار ومسؤوليات التصنيف",
        ),
        (
            "DC.C.5.1",
            "سجل يحتوي قائمة مجموعات البيانات والسجلات المحددة وأنشطة تصنيف البيانات",
        ),
    ]

    for evidence_code, provided_text in demo_cases:
        try:
            result = analyze_gap(
                evidence_code,
                provided_text,
            )
        except Exception as exc:
            warnings_and_errors.append(
                f'فشل analyze_gap لـ "{evidence_code}": {exc}'
            )
            continue

        _print_result(result)
        successful += 1

    ran_successfully = successful == len(demo_cases)

    print("\n" + "=" * 60)
    print("ملخص التشغيل التجريبي")
    print("=" * 60)

    print(
        f"هل اشتغل المحرك بنجاح؟ "
        f"{'نعم' if ran_successfully else 'لا'}"
    )

    print(
        f"عدد التجارب الناجحة: "
        f"{successful}/{len(demo_cases)}"
    )

    print(
        f"عدد warnings/errors: "
        f"{len(warnings_and_errors)}"
    )

    for item in warnings_and_errors:
        print(
            f"  [WARNING/ERROR] {item}"
        )


if __name__ == "__main__":
    main()