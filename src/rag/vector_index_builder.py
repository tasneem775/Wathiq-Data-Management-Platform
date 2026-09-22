"""
Vector Index Builder — Embeddings + ChromaDB.

يبني Vector Database محلي عبر ChromaDB من Content Chunks الجاهزة مسبقاً
(بعد استخراج النص الفعلي من صفحات PDF)، دون أي LLM أو LangChain.

المصدر: data/rag_index/dc_rag_content_index.json (قراءة فقط)
الناتج: vector_db/dc_rag_chroma/ (ChromaDB PersistentClient)
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
CONTENT_INDEX_PATH = PROJECT_ROOT / "data" / "rag_index" / "dc_rag_content_index.json"
VECTOR_DB_PATH = PROJECT_ROOT / "vector_db" / "dc_rag_chroma"
COLLECTION_NAME = "dc_rag_content_chunks"

METADATA_FIELDS = [
    "chunk_id",
    "evidence_code",
    "evidence_name",
    "mq_id",
    "level_number",
    "level_name",
    "chunk_type",
    "source_document",
    "source_path",
    "page_number",
    "source_type",
    "page_role",
    "matched_by",
    "confidence",
]


def load_content_chunks(path=CONTENT_INDEX_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_metadata(chunk, warnings):
    metadata = {}
    for field in METADATA_FIELDS:
        value = chunk.get(field)
        if value is None:
            warnings.append(f"{chunk.get('chunk_id')}: الحقل \"{field}\" غير موجود/فارغ — سيُخزَّن كسلسلة فارغة.")
            value = ""
        metadata[field] = value
    return metadata


def build_vector_index():
    warnings = []
    chunks = load_content_chunks()

    valid_chunks = []
    for chunk in chunks:
        text = chunk.get("text")
        if not text or not text.strip():
            warnings.append(f"{chunk.get('chunk_id')}: تم تجاوزه — حقل text فارغ.")
            continue
        valid_chunks.append(chunk)

    VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
    )

    ids = []
    documents = []
    metadatas = []
    for chunk in valid_chunks:
        ids.append(chunk["chunk_id"])
        documents.append(chunk["text"])
        metadatas.append(build_metadata(chunk, warnings))

    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    return chunks, valid_chunks, collection, warnings


def main():
    chunks, valid_chunks, collection, warnings = build_vector_index()
    inserted_count = collection.count()

    print(f"عدد chunks المقروءة: {len(chunks)}")
    print(f"عدد chunks التي تم إدخالها في ChromaDB: {inserted_count}")
    print(f"اسم collection: {COLLECTION_NAME}")
    print(f"مسار قاعدة ChromaDB: {VECTOR_DB_PATH}")

    if valid_chunks:
        first = collection.get(ids=[valid_chunks[0]["chunk_id"]], include=["metadatas"])
        example_metadata = first["metadatas"][0]
        print("\nمثال metadata لأول chunk:")
        print(json.dumps(example_metadata, ensure_ascii=False, indent=2))

    print(f"\nعدد warnings: {len(warnings)}")
    for warning in warnings:
        print(f"  [WARNING] {warning}")


if __name__ == "__main__":
    main()
