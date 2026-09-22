"""
Compliance Recommendation Engine — يحوّل نتائج gap_analysis_engine.py إلى توصيات
عملية قابلة للتنفيذ، بالاعتماد فقط على قواعد وقوالب محلية جاهزة.

لا يُستخدم أي LLM ولا OpenAI ولا OpenRouter ولا LangChain ولا أي API خارجي —
فقط منطق قواعد ثابت (Rule-Based) فوق ثلاثة مصادر محلية:
  1. src/evidence_assessment/gap_analysis_engine.py (analyze_gap)
  2. data/rules/compliance_rules.json               (document_type لكل دليل)
  3. data/rules/recommendation_templates.json        (نصوص التوصيات الجاهزة)
"""

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.evidence_assessment.gap_analysis_engine import analyze_gap  # noqa: E402

RULES_PATH = PROJECT_ROOT / "data" / "rules" / "compliance_rules.json"
TEMPLATES_PATH = PROJECT_ROOT / "data" / "rules" / "recommendation_templates.json"

_rules_cache = None
_templates_cache = None


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_rules():
    global _rules_cache
    if _rules_cache is None:
        _rules_cache = _load_json(RULES_PATH) if RULES_PATH.exists() else {}
    return _rules_cache


def _get_templates():
    global _templates_cache
    if _templates_cache is None:
        _templates_cache = _load_json(TEMPLATES_PATH) if TEMPLATES_PATH.exists() else {}
    return _templates_cache


def _select_recommendation_type(document_type, priority):
    """يختار نوع التوصية بناءً على نوع الوثيقة، مع تمييز إضافي للسياسات:
    بند حرج (HIGH) في Policy يعني قسماً كاملاً مفقوداً → ADD_SECTION،
    بينما بند متوسط (MEDIUM) يعني استكمال محتوى قائم → UPDATE_POLICY."""
    if document_type == "Policy":
        return "ADD_SECTION" if priority == "HIGH" else "UPDATE_POLICY"
    if document_type == "Report":
        return "PROVIDE_REPORT"
    if document_type == "List":
        return "PROVIDE_LIST"
    if document_type == "Register":
        return "PROVIDE_REGISTER"
    if document_type in ("Tool", "Evidence"):
        return "PROVIDE_EVIDENCE"
    return "ADD_REQUIRED_CONTENT"


def _page_references(references):
    pages = {r.get("page_number") for r in (references or []) if r.get("page_number") is not None}
    return sorted(pages)


def _supporting_documents(references):
    """يستخرج أسماء الوثائق (document_name) فقط من references، بدون تكرار."""
    seen = []
    for r in (references or []):
        name = r.get("document_name")
        if name and name not in seen:
            seen.append(name)
    return seen


def _build_issue_reason(criterion, category):
    """يشرح أن هذا المتطلب غير مستوفى، بناءً على كونه بنداً حرجاً (critical_missing)
    أو متوسطاً (medium_missing)."""
    if category == "critical_missing":
        return f'البند الحرج "{criterion}" ضمن متطلبات القبول غير مستوفى في الدليل المقدَّم.'
    return f'البند المتوسط "{criterion}" ضمن متطلبات القبول غير مستوفى بالكامل في الدليل المقدَّم.'


def _build_recommendation(evidence_code, criterion, priority, category, document_type, templates, result):
    recommendation_type = _select_recommendation_type(document_type, priority)
    template = templates.get(recommendation_type, "{criterion}")
    references = result.get("references")

    return {
        "evidence_code": evidence_code,
        "overall_status": result.get("overall_status"),
        "priority": priority,
        "recommendation_type": recommendation_type,
        "issue": {
            "criterion": criterion,
            "reason": _build_issue_reason(criterion, category),
            "category": category,
        },
        "action": {
            "title": recommendation_type,
            "description": template.format(criterion=criterion),
        },
        "impact": {
            "severity": priority,
            "expected_improvement": "استيفاء هذا المتطلب سيساعد في رفع مستوى الامتثال لهذا الدليل.",
        },
        "references": references or [],
        "supporting_documents": _supporting_documents(references),
    }


def generate_recommendations(evidence_code, provided_evidence_text=""):
    """يحلّل دليلاً واحداً عبر analyze_gap ثم يبني توصية لكل بند ناقص
    (critical_missing / medium_missing) مع ملخص إجمالي."""
    result = analyze_gap(evidence_code, provided_evidence_text)
    rule = _get_rules().get(evidence_code) or {}
    templates = _get_templates()
    document_type = rule.get("document_type") or result.get("document_type")

    recommendations = []
    for criterion in result.get("critical_missing", []):
        recommendations.append(
            _build_recommendation(
                evidence_code, criterion, "HIGH", "critical_missing", document_type, templates, result
            )
        )
    for criterion in result.get("medium_missing", []):
        recommendations.append(
            _build_recommendation(
                evidence_code, criterion, "MEDIUM", "medium_missing", document_type, templates, result
            )
        )

    high_priority_count = sum(1 for r in recommendations if r["priority"] == "HIGH")
    medium_priority_count = sum(1 for r in recommendations if r["priority"] == "MEDIUM")

    summary = {
        "evidence_code": evidence_code,
        "overall_status": result.get("overall_status"),
        "total_recommendations": len(recommendations),
        "high_priority_count": high_priority_count,
        "medium_priority_count": medium_priority_count,
        "needs_human_review": result.get("needs_human_review", False),
    }

    return {
        "evidence_code": evidence_code,
        "overall_status": result.get("overall_status"),
        "recommendations": recommendations,
        "summary": summary,
    }


def generate_multiple_recommendations(evidence_codes, provided_evidence_map):
    """يشغّل generate_recommendations على قائمة أكواد أدلة، باستخدام
    provided_evidence_map (dict: evidence_code -> نص الدليل المقدَّم) لكل كود."""
    provided_evidence_map = provided_evidence_map or {}
    return [
        generate_recommendations(code, provided_evidence_map.get(code, ""))
        for code in evidence_codes
    ]


def _print_case(output):
    summary = output["summary"]
    print(f"\nevidence_code: {summary['evidence_code']}")
    print("-" * 60)
    print(f"  overall_status: {summary['overall_status']}")
    print(f"  total_recommendations: {summary['total_recommendations']}")
    print(f"  high_priority_count: {summary['high_priority_count']}")
    print(f"  medium_priority_count: {summary['medium_priority_count']}")
    print("  أول 5 توصيات:")
    for rec in output["recommendations"][:5]:
        print(f"    - [{rec['priority']}] ({rec['action']['title']}) {rec['action']['description']}")


def main():
    demo_cases = {
        "DC.M.6": "سياسة تصنيف البيانات معتمدة من صاحب الصلاحية وتتضمن نطاق العمل وتاريخ الإصدار",
        "DC.C.5.1": "سجل البيانات يحتوي قائمة مجموعات البيانات والسجلات المحددة ومستويات التصنيف الممنوحة",
    }

    outputs = generate_multiple_recommendations(list(demo_cases.keys()), demo_cases)
    for output in outputs:
        _print_case(output)


if __name__ == "__main__":
    main()
