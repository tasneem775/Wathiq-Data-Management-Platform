"""
Context Builder — يحوّل نتائج hybrid_search إلى Context منظّم وجاهز
للإرسال لاحقاً إلى LLM (بدون أي استدعاء فعلي لـ LLM هنا).

لا يُستخدم LLM ولا LangChain ولا AI Agent ولا أي API خارجي، ولا يفتح أي
اتصال جديد بـ ChromaDB ولا يُنتج Embeddings مباشرة — كل ما يفعله هو إعادة
تشكيل نتائج src/rag/hybrid_retriever.py.hybrid_search() فقط.
"""

import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.hybrid_retriever import hybrid_search  # noqa: E402

DEMO_QUERIES = [
    "ما المطلوب في DC.M.6؟",
    "سجل البيانات",
    "سياسة تصنيف البيانات",
]


def build_context(query, top_k=5):
    """يبني Context منظّم من نتائج hybrid_search فقط، دون أي مصدر آخر."""
    results = hybrid_search(query, top_k=top_k)

    if results:
        strategy = results[0]["strategy"]
        detected_evidence_code = results[0]["detected_evidence_code"]
    else:
        strategy = None
        detected_evidence_code = None

    context_blocks = []
    citations = []
    for i, r in enumerate(results, start=1):
        context_blocks.append({
            "block_id": f"block_{i}",
            "evidence_code": r["evidence_code"],
            "evidence_name": r["evidence_name"],
            "chunk_type": r["chunk_type"],
            "source_document": r["source_document"],
            "page_number": r["page_number"],
            "page_role": r["page_role"],
            "text": r["text_preview"],
        })
        citations.append({
            "citation_id": f"citation_{i}",
            "evidence_code": r["evidence_code"],
            "source_document": r["source_document"],
            "page_number": r["page_number"],
            "page_role": r["page_role"],
        })

    document_names = sorted({r["source_document"] for r in results if r.get("source_document")})

    summary = {
        "result_count": len(results),
        "document_count": len(document_names),
        "document_names": document_names,
        "evidence_code_detected": detected_evidence_code is not None,
    }

    return {
        "query": query,
        "strategy": strategy,
        "detected_evidence_code": detected_evidence_code,
        "context_blocks": context_blocks,
        "citations": citations,
        "summary": summary,
    }


def _print_context(context):
    print(f"\nQuery: {context['query']}")
    print("-" * 60)
    print(f"  strategy: {context['strategy']}")
    print(f"  detected_evidence_code: {context['detected_evidence_code']}")
    print(f"  عدد context_blocks: {len(context['context_blocks'])}")

    print("  citations:")
    for c in context["citations"]:
        print(
            f"    - {c['citation_id']}: {c['evidence_code']} | "
            f"{c['source_document']} | page_number={c['page_number']} | page_role={c['page_role']}"
        )

    if context["context_blocks"]:
        first_text = context["context_blocks"][0]["text"]
        print("  أول 700 حرف من أول context_block:")
        print(f"    {first_text[:700]}")
    else:
        print("  لا توجد context_blocks.")


def main():
    warnings_and_errors = []
    successful = 0

    for query in DEMO_QUERIES:
        try:
            context = build_context(query, top_k=5)
        except Exception as exc:
            warnings_and_errors.append(f"فشل بناء Context لـ \"{query}\": {exc}")
            continue

        _print_context(context)
        successful += 1

    built_successfully = successful == len(DEMO_QUERIES)

    print("\n" + "=" * 60)
    print("ملخص التشغيل التجريبي")
    print("=" * 60)
    print(f"هل تم بناء Context بنجاح؟ {'نعم' if built_successfully else 'لا'}")
    print(f"عدد التجارب الناجحة: {successful}/{len(DEMO_QUERIES)}")
    print(f"عدد warnings/errors: {len(warnings_and_errors)}")
    for item in warnings_and_errors:
        print(f"  [WARNING/ERROR] {item}")


if __name__ == "__main__":
    main()
