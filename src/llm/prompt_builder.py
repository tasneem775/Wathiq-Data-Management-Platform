"""
Prompt Builder — يجهّز Prompt نصي منظم جاهز لإرساله لاحقاً إلى LLM، اعتماداً
حصراً على src/rag/context_builder.py.

لا يُستدعى أي LLM هنا (لا OpenAI ولا Azure OpenAI ولا Ollama)، ولا LangChain،
ولا أي API خارجي — فقط تجميع نصي (String Formatting) فوق build_context().
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
]

SECTION_DIVIDER = "=" * 60

SYSTEM_ROLE = (
    "You are an NDMO Data Governance Compliance Advisor.\n"
    "You MUST answer only using the supplied CONTEXT.\n"
    "Never use external knowledge.\n"
    "If the answer is not found in CONTEXT, explicitly state that."
)

INSTRUCTIONS = (
    "- استخدم المعلومات الموجودة في CONTEXT فقط.\n"
    "- لا تخمن.\n"
    "- لا تستخدم أي معرفة خارج السياق.\n"
    "- إذا لم تجد الإجابة، اذكر ذلك بوضوح.\n"
    "- استشهد بالمراجع والصفحات.\n"
    "- أجب بالعربية الرسمية.\n"
    "- لا تذكر معلومات غير مدعومة بالمراجع."
)

REQUIRED_OUTPUT_FORMAT = (
    "أعد الإجابة بالترتيب التالي بالضبط:\n"
    "- Executive Summary\n"
    "- Compliance Analysis\n"
    "- Required Evidence\n"
    "- References\n"
    "- Confidence Level"
)


def _build_context_section(context_blocks):
    if not context_blocks:
        return "لا توجد أي Context Blocks لهذا الاستعلام."

    parts = []
    for block in context_blocks:
        parts.append(
            f"[{block['block_id']}]\n"
            f"Evidence Code: {block['evidence_code']}\n"
            f"Evidence Name: {block['evidence_name']}\n"
            f"Chunk Type: {block['chunk_type']}\n"
            f"Source Document: {block['source_document']}\n"
            f"Page Number: {block['page_number']}\n"
            f"Page Role: {block['page_role']}\n"
            f"Text: {block['text']}"
        )
    return "\n\n".join(parts)


def _build_citations_section(citations):
    if not citations:
        return "لا توجد أي Citations لهذا الاستعلام."

    lines = []
    for c in citations:
        lines.append(
            f"[{c['citation_id']}] {c['evidence_code']} | {c['source_document']} | "
            f"page_number={c['page_number']} | page_role={c['page_role']}"
        )
    return "\n".join(lines)


def build_prompt(query, top_k=5):
    """يبني Prompt نصي منظم من نتائج build_context فقط، دون أي استدعاء لـ LLM."""
    context = build_context(query, top_k=top_k)

    context_section = _build_context_section(context["context_blocks"])
    citations_section = _build_citations_section(context["citations"])

    prompt = (
        f"{SECTION_DIVIDER}\n"
        f"1. SYSTEM ROLE\n"
        f"{SECTION_DIVIDER}\n\n"
        f"{SYSTEM_ROLE}\n\n"
        f"{SECTION_DIVIDER}\n"
        f"2. INSTRUCTIONS\n"
        f"{SECTION_DIVIDER}\n\n"
        f"{INSTRUCTIONS}\n\n"
        f"{SECTION_DIVIDER}\n"
        f"3. USER QUESTION\n"
        f"{SECTION_DIVIDER}\n\n"
        f"{query}\n\n"
        f"{SECTION_DIVIDER}\n"
        f"4. CONTEXT\n"
        f"{SECTION_DIVIDER}\n\n"
        f"{context_section}\n\n"
        f"{SECTION_DIVIDER}\n"
        f"5. CITATIONS\n"
        f"{SECTION_DIVIDER}\n\n"
        f"{citations_section}\n\n"
        f"{SECTION_DIVIDER}\n"
        f"6. REQUIRED OUTPUT FORMAT\n"
        f"{SECTION_DIVIDER}\n\n"
        f"{REQUIRED_OUTPUT_FORMAT}\n"
    )

    return {
        "query": query,
        "prompt": prompt,
        "context_block_count": len(context["context_blocks"]),
        "citation_count": len(context["citations"]),
    }


def _print_summary(result):
    print(f"\nQuery: {result['query']}")
    print("-" * 60)
    print(f"  طول الـ Prompt (حرف): {len(result['prompt'])}")
    print(f"  عدد Context Blocks: {result['context_block_count']}")
    print(f"  عدد Citations: {result['citation_count']}")
    print("  أول 1000 حرف من الـ Prompt:")
    print(result["prompt"][:1000])


def main():
    warnings_and_errors = []
    successful = 0

    for query in DEMO_QUERIES:
        try:
            result = build_prompt(query)
        except Exception as exc:
            warnings_and_errors.append(f"فشل بناء Prompt لـ \"{query}\": {exc}")
            continue

        _print_summary(result)
        successful += 1

    built_successfully = successful == len(DEMO_QUERIES)

    print("\n" + "=" * 60)
    print("ملخص التشغيل التجريبي")
    print("=" * 60)
    print(f"هل تم بناء الـ Prompt بنجاح؟ {'نعم' if built_successfully else 'لا'}")
    print(f"عدد التجارب الناجحة: {successful}/{len(DEMO_QUERIES)}")
    print(f"عدد warnings/errors: {len(warnings_and_errors)}")
    for item in warnings_and_errors:
        print(f"  [WARNING/ERROR] {item}")


if __name__ == "__main__":
    main()
