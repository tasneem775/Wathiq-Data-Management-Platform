"""
Hybrid Retriever — يدمج Retrieval Router مع Semantic Retriever لتحسين دقة
الاسترجاع.

المشكلة التي يعالجها: semantic_retriever.py يبحث في ChromaDB مباشرة على كل
الـ Content Chunks، وبعض الصفحات (خصوصاً Summary Page) تحتوي على أدلة متعددة
بنفس النص الحرفي تقريباً، فيصبح البحث الدلالي الخام غير دقيق في تحديد الدليل
الصحيح.

المنطق:
1. إذا كان الاستعلام يحتوي كود دليل صريح (مثل DC.M.6) -> فلترة Chroma على هذا
   الكود فقط عبر src/rag/retrieval_router.py، مع إعطاء أولوية لأنواع
   الـ chunk الأكثر تحديداً (detailed_requirement_content،
   official_reference_content، supporting_policy_content) على حساب
   reference_summary_content.
2. إذا لم يوجد كود صريح: حاول مطابقة الاستعلام مع evidence_name من
   data/knowledge_graph/dc_knowledge_graph.json (عبر Retrieval Router الذي
   يحمّله). عند وجود تطابق جزئي قوي، يُستخدم كود الدليل المطابق كفلتر بنفس
   منطق الحالة الأولى.
3. إذا لم يُعثر على كود أو اسم دليل مطابق: رجوع كامل إلى semantic_search بدون
   أي فلتر (كما في semantic_retriever.py).

لا يُستخدم LLM ولا LangChain ولا AI Agent ولا أي API خارجي — فقط قواعد نصية
ثابتة فوق ChromaDB المحلية.
"""

import re
import sys
import unicodedata
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.retrieval_router import RetrievalRouter, EVIDENCE_CODE_PATTERN  # noqa: E402
from src.rag.semantic_retriever import semantic_search  # noqa: E402

PRIORITY_TIER = {
    "detailed_requirement_content": 0,
    "official_reference_content": 0,
    "supporting_policy_content": 0,
    "reference_summary_content": 1,
}

STOPWORDS = {
    "ما", "هل", "في", "من", "على", "إلى", "عن", "هو", "هي",
    "التي", "الذي", "المطلوب", "و", "أو", "مع", "عبر", "كل",
    # كلمات عامة متكررة في كل أدلة مجال تصنيف البيانات تقريباً، فلا تميّز
    # دليلاً عن آخر ولا ينبغي أن تُحتسب ضمن تطابق الأسماء الجزئي.
    "تصنيف", "البيانات",
}

STRONG_MATCH_THRESHOLD = 0.6
FETCH_POOL_SIZE = 50

DEMO_QUERIES = [
    "سياسة تصنيف البيانات",
    "ما المطلوب لتعريف تصنيف البيانات؟",
    "سجل البيانات",
    "تقرير مراقبة مؤشرات الأداء لتصنيف البيانات",
    "أداة أتمتة تصنيف البيانات",
    "ما المطلوب في DC.M.6؟",
]

_router = None


def _get_router():
    global _router
    if _router is None:
        _router = RetrievalRouter()
    return _router


def _normalize(text):
    if not text:
        return ""
    return unicodedata.normalize("NFC", text).strip()


def _tokenize(text):
    text = re.sub(r"[؟?.,:;!\"'()،]", " ", text)
    return [t for t in text.split() if t]


def _content_tokens(text):
    return [t for t in _tokenize(text) if t not in STOPWORDS]


def _match_evidence_name(query, nodes):
    """يبحث عن أقوى تطابق جزئي بين query وأسماء الأدلة (evidence_name).

    يعيد (evidence_code, score) أو (None, 0.0) إذا لم يوجد تطابق قوي بما
    يكفي (>= STRONG_MATCH_THRESHOLD).
    """
    query_norm = _normalize(query)
    query_tokens = set(_content_tokens(query_norm))
    if not query_tokens:
        return None, 0.0

    best_code = None
    best_score = 0.0

    for node in nodes:
        name_norm = _normalize(node["evidence_name"])
        if not name_norm:
            continue

        if name_norm == query_norm:
            score = 1.0
        elif name_norm in query_norm or query_norm in name_norm:
            score = 0.95
        else:
            name_tokens = set(_content_tokens(name_norm))
            if not name_tokens:
                continue
            overlap = query_tokens & name_tokens
            if not overlap:
                continue
            score = len(overlap) / len(query_tokens)

        if score > best_score:
            best_score = score
            best_code = node["evidence_code"]

    if best_code is not None and best_score >= STRONG_MATCH_THRESHOLD:
        return best_code, best_score
    return None, 0.0


def _detect_evidence_code(query, router):
    match = EVIDENCE_CODE_PATTERN.search(query)
    if match:
        candidate = match.group(0).upper()
        if candidate in router.nodes_by_code:
            return candidate
    return None


def _search_within_evidence(query, evidence_code, top_k):
    pool = semantic_search(query, top_k=FETCH_POOL_SIZE, filters={"evidence_code": evidence_code})
    pool.sort(key=lambda r: (PRIORITY_TIER.get(r["chunk_type"], 0), r["distance"]))
    return pool[:top_k]


def hybrid_search(query, top_k=5):
    """بحث هجين: يوجّه الاستعلام إلى دليل محدد عند الإمكان قبل أي Vector Search عام."""
    router = _get_router()

    strategy = "semantic_only"
    detected_evidence_code = _detect_evidence_code(query, router)
    if detected_evidence_code:
        strategy = "evidence_code"
    else:
        matched_code, _ = _match_evidence_name(query, router.nodes)
        if matched_code:
            detected_evidence_code = matched_code
            strategy = "evidence_name_match"

    if detected_evidence_code:
        raw_results = _search_within_evidence(query, detected_evidence_code, top_k)
    else:
        raw_results = semantic_search(query, top_k=top_k)

    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append({
            "rank": rank,
            "strategy": strategy,
            "detected_evidence_code": detected_evidence_code,
            "evidence_code": r["evidence_code"],
            "evidence_name": r["evidence_name"],
            "chunk_type": r["chunk_type"],
            "source_document": r["source_document"],
            "page_number": r["page_number"],
            "page_role": r["page_role"],
            "distance": r["distance"],
            "text_preview": r["text_preview"],
        })

    return results


def _print_results(query, results):
    print(f"\nQuery: {query}")
    print("-" * 60)
    if not results:
        print("  لا توجد نتائج.")
        return
    for r in results:
        print(f"  [{r['rank']}] strategy={r['strategy']} | detected_evidence_code={r['detected_evidence_code']}")
        print(f"      evidence_code: {r['evidence_code']} | evidence_name: {r['evidence_name']}")
        print(f"      chunk_type: {r['chunk_type']} | distance: {r['distance']:.4f}")
        print(f"      source_document: {r['source_document']} | page_number: {r['page_number']} | page_role: {r['page_role']}")
        print(f"      text_preview: {r['text_preview'][:150].strip()}...")
        print()


def main():
    per_query_summary = []

    for query in DEMO_QUERIES:
        results = hybrid_search(query, top_k=5)
        _print_results(query, results)
        top = results[0] if results else None
        per_query_summary.append((query, top))

    print("\n" + "=" * 60)
    print("ملخص التشغيل التجريبي")
    print("=" * 60)

    for query, top in per_query_summary:
        print(f"\nQuery: {query}")
        if top:
            print(f"  الاستراتيجية المستخدمة: {top['strategy']}")
            print(f"  detected_evidence_code: {top['detected_evidence_code']}")
            print(
                f"  أفضل نتيجة: evidence_code={top['evidence_code']} | "
                f"source_document={top['source_document']} | page_number={top['page_number']}"
            )
        else:
            print("  لا توجد نتائج.")


if __name__ == "__main__":
    main()
