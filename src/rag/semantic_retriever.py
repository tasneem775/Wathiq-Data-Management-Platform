"""
Semantic Retriever — Semantic Search Console فوق ChromaDB الموجودة مسبقاً.

يفتح قاعدة ChromaDB المبنية بواسطة src/rag/vector_index_builder.py
(vector_db/dc_rag_chroma/ ، collection = dc_rag_content_chunks) وينفذ بحثاً
دلالياً على النصوص المخزنة، دون أي LLM أو LangChain أو AI Agent أو أي API
خارجي — فقط استعلام Vector Search محلي عبر ChromaDB.
"""

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

try:
    import chromadb
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
except ImportError:
    print(
        "ChromaDB غير مثبت في بيئة Python الحالية.\n"
        "لتثبيته شغّل:\n"
        "  pip install chromadb\n"
        "لم يتم تعديل أو إنشاء أي شيء."
    )
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_DB_PATH = PROJECT_ROOT / "vector_db" / "dc_rag_chroma"
COLLECTION_NAME = "dc_rag_content_chunks"

DEMO_QUERIES = [
    "سياسة تصنيف البيانات",
    "ما المطلوب لتعريف تصنيف البيانات؟",
    "سجل البيانات",
    "تقرير مراقبة مؤشرات الأداء لتصنيف البيانات",
    "أداة أتمتة تصنيف البيانات",
]

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection

    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
    )
    _client, _collection = client, collection
    return collection


def semantic_search(query, top_k=5, filters=None):
    """بحث دلالي على Content Chunks المخزنة في ChromaDB.

    يعيد قائمة نتائج مرتبة، كل نتيجة تحوي rank و distance (الأقل = الأقرب
    دلالياً) بالإضافة إلى metadata الدليل ومعاينة أول 500 حرف من النص.
    """
    collection = _get_collection()

    query_kwargs = {
        "query_texts": [query],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if filters:
        query_kwargs["where"] = filters

    raw = collection.query(**query_kwargs)

    ids = raw.get("ids", [[]])[0]
    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    results = []
    for rank, (chunk_id, doc_text, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances), start=1
    ):
        text = doc_text or ""
        results.append({
            "rank": rank,
            "distance": distance,
            "chunk_id": chunk_id,
            "evidence_code": metadata.get("evidence_code"),
            "evidence_name": metadata.get("evidence_name"),
            "mq_id": metadata.get("mq_id"),
            "level_number": metadata.get("level_number"),
            "level_name": metadata.get("level_name"),
            "chunk_type": metadata.get("chunk_type"),
            "source_document": metadata.get("source_document"),
            "page_number": metadata.get("page_number"),
            "page_role": metadata.get("page_role"),
            "text_preview": text[:500],
        })

    return results


def _print_results(query, results):
    print(f"\nQuery: {query}")
    print("-" * 60)
    if not results:
        print("  لا توجد نتائج.")
        return
    for r in results:
        print(f"  [{r['rank']}] distance={r['distance']:.4f} | {r['chunk_id']}")
        print(f"      evidence_code: {r['evidence_code']} | evidence_name: {r['evidence_name']}")
        print(f"      mq_id: {r['mq_id']} | level: {r['level_number']} ({r['level_name']}) | chunk_type: {r['chunk_type']}")
        print(f"      source_document: {r['source_document']} | page_number: {r['page_number']} | page_role: {r['page_role']}")
        print(f"      text_preview: {r['text_preview'][:150].strip()}...")
        print()


def main():
    warnings_and_errors = []

    try:
        _get_collection()
        opened_successfully = True
    except Exception as exc:
        opened_successfully = False
        warnings_and_errors.append(f"تعذر فتح ChromaDB/collection: {exc}")

    print(f"هل تم فتح ChromaDB بنجاح؟ {'نعم' if opened_successfully else 'لا'}")

    per_query_summary = []

    if opened_successfully:
        for query in DEMO_QUERIES:
            try:
                results = semantic_search(query, top_k=5)
            except Exception as exc:
                warnings_and_errors.append(f"فشل البحث عن \"{query}\": {exc}")
                per_query_summary.append((query, 0, None))
                continue

            _print_results(query, results)

            top = results[0] if results else None
            per_query_summary.append((query, len(results), top))

    print("\n" + "=" * 60)
    print("ملخص التشغيل التجريبي")
    print("=" * 60)
    print(f"هل تم فتح ChromaDB بنجاح؟ {'نعم' if opened_successfully else 'لا'}")

    for query, count, top in per_query_summary:
        print(f"\nQuery: {query}")
        print(f"  عدد النتائج: {count}")
        if top:
            print(
                f"  أفضل نتيجة: evidence_code={top['evidence_code']} | "
                f"source_document={top['source_document']} | page_number={top['page_number']}"
            )
        else:
            print("  أفضل نتيجة: لا يوجد")

    print(f"\nعدد warnings/errors: {len(warnings_and_errors)}")
    for item in warnings_and_errors:
        print(f"  [WARNING/ERROR] {item}")


if __name__ == "__main__":
    main()
