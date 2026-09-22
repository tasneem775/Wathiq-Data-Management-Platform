"""
Compliance Advisor — أول وكيل استشاري يعتمد حصراً على
src/rag/context_builder.py لبناء إجابات منظمة حول متطلبات الامتثال.

لا يُستخدم أي LLM هنا حالياً — الإجابة Rule-Based بالكامل، مبنية فقط على
context_blocks و citations القادمة من build_context(). لا استدعاء مباشر
لـ LangChain أو ChromaDB أو Embeddings، ولا أي تعديل على data/ أو طبقات RAG.
"""

import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.context_builder import build_context  # noqa: E402

DEMO_QUERIES = [
    "ما المطلوب في DC.M.6؟",
    "سجل البيانات",
    "ما المطلوب لتعريف تصنيف البيانات؟",
]

HIGH_CONFIDENCE_STRATEGIES = {"evidence_code", "evidence_name_match"}


def _evidence_name_from_blocks(context_blocks, evidence_code):
    for block in context_blocks:
        if block["evidence_code"] == evidence_code and block.get("evidence_name"):
            return block["evidence_name"]
    return None


def _required_evidence_from_blocks(context_blocks):
    """يستخرج متطلبات الدليل من نصوص detailed_requirement/official_reference/
    supporting_policy فقط (أكثر أنواع الـ chunk تحديداً لمتطلبات القبول)."""
    preferred_types = {
        "detailed_requirement_content",
        "official_reference_content",
        "supporting_policy_content",
    }
    requirements = []
    for block in context_blocks:
        if block["chunk_type"] in preferred_types:
            requirements.append({
                "block_id": block["block_id"],
                "chunk_type": block["chunk_type"],
                "text": block["text"],
            })
    if not requirements:
        # لا توجد نصوص متطلبات دقيقة، استخدم كل ما توفر كحد أدنى
        requirements = [
            {
                "block_id": b["block_id"],
                "chunk_type": b["chunk_type"],
                "text": b["text"],
            }
            for b in context_blocks
        ]
    return requirements


def _confidence_level(strategy, result_count):
    if result_count == 0:
        return "منعدمة"
    if strategy in HIGH_CONFIDENCE_STRATEGIES:
        return "عالية"
    return "متوسطة"


def _build_answer_with_code(query, context, evidence_name):
    code = context["detected_evidence_code"]
    lines = []
    if evidence_name:
        lines.append(f"الدليل المكتشف: {code} — {evidence_name}")
    else:
        lines.append(f"الدليل المكتشف: {code}")

    requirements = _required_evidence_from_blocks(context["context_blocks"])
    if requirements:
        lines.append("المتطلبات المستخرجة من النصوص المسترجعة:")
        for req in requirements:
            snippet = req["text"].strip().replace("\n", " ")
            lines.append(f"  - [{req['block_id']}] ({req['chunk_type']}): {snippet[:400]}")
    else:
        lines.append("لم يتم العثور على نصوص متطلبات مفصّلة لهذا الدليل ضمن السياق المسترجع.")

    return "\n".join(lines)


def _build_answer_without_code(query, context):
    lines = [
        "السؤال عام ولم يتم تحديد كود دليل أو اسم دليل مطابق بثقة كافية.",
        "لتحديد إجابة دقيقة، يُرجى تضمين كود الدليل (مثال: DC.M.6) أو اسمه الكامل في السؤال.",
    ]
    blocks = context["context_blocks"]
    if blocks:
        lines.append("أقرب النتائج المسترجعة (semantic search بدون فلترة):")
        for b in blocks:
            snippet = b["text"].strip().replace("\n", " ")
            lines.append(
                f"  - [{b['block_id']}] {b['evidence_code']} — {b['evidence_name']} "
                f"({b['chunk_type']}): {snippet[:300]}"
            )
    else:
        lines.append("لا توجد أي نتائج مسترجعة لهذا الاستعلام.")

    return "\n".join(lines)


def advise(query, top_k=5):
    """يبني تقرير استشاري منظم لسؤال امتثال واحد، اعتماداً على build_context فقط."""
    context = build_context(query, top_k=top_k)

    detected_evidence_code = context["detected_evidence_code"]
    strategy = context["strategy"]
    context_blocks = context["context_blocks"]
    citations = context["citations"]

    if detected_evidence_code:
        evidence_name = _evidence_name_from_blocks(context_blocks, detected_evidence_code)
        answer = _build_answer_with_code(query, context, evidence_name)
        required_evidence = _required_evidence_from_blocks(context_blocks)
        notes = "تم تحديد الدليل تلقائياً (strategy={}).".format(strategy)
    else:
        answer = _build_answer_without_code(query, context)
        required_evidence = []
        notes = "لم يتم اكتشاف كود/اسم دليل بثقة كافية — الإجابة مبنية على أقرب نتائج دلالية عامة."

    confidence_level = _confidence_level(strategy, context["summary"]["result_count"])

    return {
        "query": query,
        "strategy": strategy,
        "detected_evidence_code": detected_evidence_code,
        "answer": answer,
        "required_evidence": required_evidence,
        "references": citations,
        "confidence_level": confidence_level,
        "notes": notes,
    }


def _print_report(report):
    print(f"\nQuery: {report['query']}")
    print("-" * 60)
    print(f"  strategy: {report['strategy']}")
    print(f"  detected_evidence_code: {report['detected_evidence_code']}")
    print(f"  confidence_level: {report['confidence_level']}")
    print(f"  notes: {report['notes']}")
    print("  answer:")
    for line in report["answer"].splitlines():
        print(f"    {line}")
    print(f"  عدد required_evidence: {len(report['required_evidence'])}")
    print("  references:")
    for ref in report["references"]:
        print(
            f"    - {ref['citation_id']}: {ref['evidence_code']} | "
            f"{ref['source_document']} | page_number={ref['page_number']} | page_role={ref['page_role']}"
        )


def main():
    warnings_and_errors = []
    successful = 0

    for query in DEMO_QUERIES:
        try:
            report = advise(query)
        except Exception as exc:
            warnings_and_errors.append(f"فشل بناء advise لـ \"{query}\": {exc}")
            continue

        _print_report(report)
        successful += 1

    ran_successfully = successful == len(DEMO_QUERIES)

    print("\n" + "=" * 60)
    print("ملخص التشغيل التجريبي")
    print("=" * 60)
    print(f"هل اشتغل advisor بنجاح؟ {'نعم' if ran_successfully else 'لا'}")
    print(f"عدد التجارب الناجحة: {successful}/{len(DEMO_QUERIES)}")
    print(f"عدد warnings/errors: {len(warnings_and_errors)}")
    for item in warnings_and_errors:
        print(f"  [WARNING/ERROR] {item}")


if __name__ == "__main__":
    main()
