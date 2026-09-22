"""
LLM Gateway — بوابة موحدة لاستقبال Prompt من src/llm/prompt_builder.py
وتجهيز مكان استدعاء نموذج LLM لاحقاً.

حالياً لا يوجد أي استدعاء فعلي لأي نموذج أو API خارجي (لا OpenAI ولا Azure
OpenAI ولا Ollama ولا LangChain) — فقط provider="mock" يبني الـ Prompt
ويعيد استجابة منظمة توضّح ذلك.
"""

import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.llm.prompt_builder import build_prompt  # noqa: E402

DEMO_QUERIES = [
    "ما المطلوب في DC.M.6؟",
    "سجل البيانات",
]

PREVIEW_LENGTH = 1500


def _generate_mock(query, top_k):
    built = build_prompt(query, top_k=top_k)
    prompt = built["prompt"]

    return {
        "query": query,
        "provider": "mock",
        "prompt_length": len(prompt),
        "status": "ok",
        "message": "لم يتم استدعاء أي نموذج LLM فعلي — تم فقط بناء الـ Prompt وإعادته (وضع mock).",
        "prompt_preview": prompt[:PREVIEW_LENGTH],
    }


def _generate_unsupported(query, provider):
    return {
        "query": query,
        "provider": provider,
        "prompt_length": 0,
        "status": "not_enabled",
        "message": f"المزود '{provider}' غير مفعل حالياً. المزود المدعوم الوحيد حالياً هو 'mock'.",
        "prompt_preview": "",
    }


def generate_answer(query, provider="mock", top_k=5):
    """يستقبل query ويبني الـ Prompt عبر build_prompt، دون أي استدعاء فعلي لأي LLM."""
    if provider == "mock":
        return _generate_mock(query, top_k)
    return _generate_unsupported(query, provider)


def _print_response(response):
    print(f"\nQuery: {response['query']}")
    print("-" * 60)
    print(f"  provider: {response['provider']}")
    print(f"  status: {response['status']}")
    print(f"  prompt_length: {response['prompt_length']}")
    print(f"  message: {response['message']}")
    print("  أول 700 حرف من prompt_preview:")
    print(response["prompt_preview"][:700])


def main():
    warnings_and_errors = []
    successful = 0

    for query in DEMO_QUERIES:
        try:
            response = generate_answer(query, provider="mock")
        except Exception as exc:
            warnings_and_errors.append(f"فشل generate_answer لـ \"{query}\": {exc}")
            continue

        _print_response(response)
        successful += 1

    ran_successfully = successful == len(DEMO_QUERIES)

    print("\n" + "=" * 60)
    print("ملخص التشغيل التجريبي")
    print("=" * 60)
    print(f"هل اشتغلت البوابة بنجاح؟ {'نعم' if ran_successfully else 'لا'}")
    print(f"عدد التجارب الناجحة: {successful}/{len(DEMO_QUERIES)}")
    print(f"عدد warnings/errors: {len(warnings_and_errors)}")
    for item in warnings_and_errors:
        print(f"  [WARNING/ERROR] {item}")


if __name__ == "__main__":
    main()
