"""
RAG Index Builder — Phase 3, Step 1.

يبني نوعين من RAG Index Data:

1. Metadata Index — يوصف كل reference (وثيقة/صفحة) دون استخراج نص فعلي.
   المصدر: data/knowledge_graph/dc_knowledge_graph.json
   الناتج: data/rag_index/dc_rag_metadata_index.json

2. Content Index — يستخرج النص الحقيقي من صفحات ملفات PDF المرجعية عبر PyMuPDF.
   المصدر: data/knowledge_graph/dc_knowledge_graph.json + knowledge_base/knowledge_sources.json
   الناتج: data/rag_index/dc_rag_content_index.json
   الأخطاء غير القاتلة تُسجَّل في: data/rag_index/dc_rag_content_warnings.json

بدون LLM، بدون Embeddings، بدون LangChain/ChromaDB.
"""

import json
import sys
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_GRAPH_PATH = PROJECT_ROOT / "data" / "knowledge_graph" / "dc_knowledge_graph.json"
KNOWLEDGE_SOURCES_PATH = PROJECT_ROOT / "knowledge_base" / "knowledge_sources.json"
KNOWLEDGE_BASE_ROOT = PROJECT_ROOT / "knowledge_base"

METADATA_OUTPUT_PATH = PROJECT_ROOT / "data" / "rag_index" / "dc_rag_metadata_index.json"
CONTENT_OUTPUT_PATH = PROJECT_ROOT / "data" / "rag_index" / "dc_rag_content_index.json"
WARNINGS_OUTPUT_PATH = PROJECT_ROOT / "data" / "rag_index" / "dc_rag_content_warnings.json"

METADATA_PAGE_ROLE_TO_CHUNK_TYPE = {
    "Summary Page": "reference_summary",
    "Detailed Requirement Page": "detailed_requirement_reference",
    "Official Maturity Reference": "official_reference",
    "Supporting Policy Page": "supporting_policy_reference",
}

CONTENT_PAGE_ROLE_TO_CHUNK_TYPE = {
    "Summary Page": "reference_summary_content",
    "Detailed Requirement Page": "detailed_requirement_content",
    "Official Maturity Reference": "official_reference_content",
    "Supporting Policy Page": "supporting_policy_content",
}


# ---------------------------------------------------------------------------
# Metadata Index (Step 1 — unchanged behaviour, renamed output file)
# ---------------------------------------------------------------------------

def _metadata_chunk(evidence, chunk_type, chunk_index, text,
                     source_document=None, page_number=None,
                     source_type=None, page_role=None):
    return {
        "chunk_id": f"{evidence['evidence_code']}::{chunk_type}::{chunk_index}",
        "evidence_code": evidence["evidence_code"],
        "evidence_name": evidence["evidence_name"],
        "mq_id": evidence["mq_id"],
        "level_number": evidence["level"]["number"],
        "level_name": evidence["level"]["name"],
        "chunk_type": chunk_type,
        "text": text,
        "source_document": source_document,
        "page_number": page_number,
        "source_type": source_type,
        "page_role": page_role,
    }


def build_metadata_chunks_for_evidence(evidence):
    chunks = []

    if evidence.get("maturity_requirement"):
        chunks.append(
            _metadata_chunk(
                evidence,
                "maturity_requirement",
                1,
                evidence["maturity_requirement"],
            )
        )

    acceptance_criteria = evidence.get("acceptance_criteria") or []
    if acceptance_criteria:
        chunks.append(
            _metadata_chunk(
                evidence,
                "acceptance_criteria",
                1,
                "\n".join(acceptance_criteria),
            )
        )

    per_type_counter = {}
    for reference in evidence.get("references", []):
        chunk_type = METADATA_PAGE_ROLE_TO_CHUNK_TYPE.get(reference.get("page_role"))
        if chunk_type is None:
            continue

        per_type_counter[chunk_type] = per_type_counter.get(chunk_type, 0) + 1
        document_name = reference.get("document_name")
        page_number = reference.get("page_number")
        source_type = reference.get("source_type")
        page_role = reference.get("page_role")

        text = (
            f"مرجع لدليل {evidence['evidence_code']} ({evidence['evidence_name']}) "
            f"من نوع \"{source_type}\" في الوثيقة \"{document_name}\" "
            f"صفحة {page_number} — دور الصفحة: {page_role}."
        )

        chunks.append(
            _metadata_chunk(
                evidence,
                chunk_type,
                per_type_counter[chunk_type],
                text,
                source_document=document_name,
                page_number=page_number,
                source_type=source_type,
                page_role=page_role,
            )
        )

    return chunks


def build_metadata_index(nodes):
    all_chunks = []
    for evidence in nodes:
        all_chunks.extend(build_metadata_chunks_for_evidence(evidence))
    return all_chunks


# ---------------------------------------------------------------------------
# Content Index (Step 2 — real text extraction via PyMuPDF)
# ---------------------------------------------------------------------------

def _normalize(name):
    return unicodedata.normalize("NFC", name).strip()


def load_knowledge_sources(path=KNOWLEDGE_SOURCES_PATH):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    sources_by_name = {}
    for source in data.get("knowledge_sources", []):
        source_name = source.get("source_name")
        if source_name:
            sources_by_name[_normalize(source_name)] = source.get("file_path")
    return sources_by_name


def _resolve_path_on_disk(relative_path_str):
    """Resolve a recorded relative path to the real file on disk.

    Handles Unicode normalization mismatches (NFC vs NFD) between JSON-recorded
    file names and actual filesystem entries.
    """
    candidate = PROJECT_ROOT / relative_path_str
    if candidate.exists():
        return candidate

    target_name = _normalize(candidate.name)

    parent = candidate.parent
    if parent.exists():
        for entry in parent.iterdir():
            if entry.is_file() and _normalize(entry.name) == target_name:
                return entry

    if KNOWLEDGE_BASE_ROOT.exists():
        for entry in KNOWLEDGE_BASE_ROOT.rglob("*.pdf"):
            if _normalize(entry.name) == target_name:
                return entry

    return None


def resolve_source_path(document_name, sources_by_name, path_cache, warnings):
    normalized_name = _normalize(document_name) if document_name else ""

    if normalized_name in path_cache:
        return path_cache[normalized_name]

    relative_path_str = sources_by_name.get(normalized_name)
    if relative_path_str is None:
        warnings.append(
            f"لا يوجد مصدر معرّف في knowledge_sources.json للوثيقة \"{document_name}\"."
        )
        path_cache[normalized_name] = None
        return None

    resolved = _resolve_path_on_disk(relative_path_str)
    if resolved is None:
        warnings.append(
            f"تعذر إيجاد ملف PDF على القرص للوثيقة \"{document_name}\" "
            f"(المسار المسجل: {relative_path_str})."
        )

    path_cache[normalized_name] = resolved
    return resolved


def extract_page_text(pdf_path, page_number, doc_cache, warnings, context_label):
    path_key = str(pdf_path)
    doc = doc_cache.get(path_key)

    if doc is None and path_key not in doc_cache:
        try:
            doc = fitz.open(pdf_path)
        except Exception as exc:
            warnings.append(
                f"تعذر فتح ملف PDF \"{pdf_path}\" لأجل {context_label}: {exc}"
            )
            doc = None
        doc_cache[path_key] = doc

    if doc is None:
        return None

    if page_number is None:
        warnings.append(f"رقم الصفحة غير محدد لأجل {context_label}.")
        return None

    page_index = page_number - 1
    if page_index < 0 or page_index >= doc.page_count:
        warnings.append(
            f"رقم الصفحة {page_number} خارج نطاق الملف \"{pdf_path}\" "
            f"(عدد الصفحات: {doc.page_count}) لأجل {context_label}."
        )
        return None

    try:
        text = doc.load_page(page_index).get_text("text")
    except Exception as exc:
        warnings.append(
            f"تعذر استخراج نص الصفحة {page_number} من \"{pdf_path}\" لأجل {context_label}: {exc}"
        )
        return None

    if not text or not text.strip():
        warnings.append(
            f"النص المستخرج من الصفحة {page_number} في \"{pdf_path}\" فارغ لأجل {context_label}."
        )
        return None

    return text.strip()


def build_content_chunks_for_evidence(evidence, sources_by_name, path_cache, doc_cache, warnings):
    chunks = []
    per_type_counter = {}

    for reference in evidence.get("references", []):
        page_role = reference.get("page_role")
        chunk_type = CONTENT_PAGE_ROLE_TO_CHUNK_TYPE.get(page_role)
        if chunk_type is None:
            warnings.append(
                f"page_role غير معروف \"{page_role}\" لدليل {evidence['evidence_code']}."
            )
            continue

        document_name = reference.get("document_name")
        page_number = reference.get("page_number")
        source_type = reference.get("source_type")
        matched_by = reference.get("matched_by")
        confidence = reference.get("confidence")
        context_label = f"{evidence['evidence_code']} / {document_name} / صفحة {page_number}"

        pdf_path = resolve_source_path(document_name, sources_by_name, path_cache, warnings)
        if pdf_path is None:
            continue

        text = extract_page_text(pdf_path, page_number, doc_cache, warnings, context_label)
        if text is None:
            continue

        per_type_counter[chunk_type] = per_type_counter.get(chunk_type, 0) + 1
        chunks.append({
            "chunk_id": f"{evidence['evidence_code']}::{chunk_type}::{per_type_counter[chunk_type]}",
            "evidence_code": evidence["evidence_code"],
            "evidence_name": evidence["evidence_name"],
            "mq_id": evidence["mq_id"],
            "level_number": evidence["level"]["number"],
            "level_name": evidence["level"]["name"],
            "chunk_type": chunk_type,
            "text": text,
            "source_document": document_name,
            "source_path": pdf_path.relative_to(PROJECT_ROOT).as_posix(),
            "page_number": page_number,
            "source_type": source_type,
            "page_role": page_role,
            "matched_by": matched_by,
            "confidence": confidence,
        })

    return chunks


def build_content_index(nodes):
    sources_by_name = load_knowledge_sources()
    path_cache = {}
    doc_cache = {}
    warnings = []

    all_chunks = []
    try:
        for evidence in nodes:
            all_chunks.extend(
                build_content_chunks_for_evidence(
                    evidence, sources_by_name, path_cache, doc_cache, warnings
                )
            )
    finally:
        for doc in doc_cache.values():
            if doc is not None:
                doc.close()

    return all_chunks, warnings


# ---------------------------------------------------------------------------
# Shared I/O
# ---------------------------------------------------------------------------

def load_knowledge_graph_nodes(path=KNOWLEDGE_GRAPH_PATH):
    with open(path, encoding="utf-8") as f:
        knowledge_graph = json.load(f)
    return knowledge_graph.get("nodes", [])


def save_json(payload, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    nodes = load_knowledge_graph_nodes()

    metadata_chunks = build_metadata_index(nodes)
    save_json(metadata_chunks, METADATA_OUTPUT_PATH)

    content_chunks, warnings = build_content_index(nodes)
    save_json(content_chunks, CONTENT_OUTPUT_PATH)
    save_json(warnings, WARNINGS_OUTPUT_PATH)

    content_counts_by_type = {}
    for chunk in content_chunks:
        content_counts_by_type[chunk["chunk_type"]] = content_counts_by_type.get(chunk["chunk_type"], 0) + 1

    print(f"عدد الأدلة المقروءة: {len(nodes)}")
    print(f"عدد metadata chunks: {len(metadata_chunks)}")
    print(f"عدد content chunks: {len(content_chunks)}")
    print("عدد content chunks لكل chunk_type:")
    for chunk_type, count in sorted(content_counts_by_type.items()):
        print(f"  - {chunk_type}: {count}")
    print(f"عدد warnings: {len(warnings)}")

    print("\nمثال كامل لـ DC.M.6 من content chunks:")
    example_chunks = [c for c in content_chunks if c["evidence_code"] == "DC.M.6"]
    print(json.dumps(example_chunks, ensure_ascii=False, indent=2))

    print("\nمسارات الملفات الناتجة:")
    print(f"  - Metadata Index: {METADATA_OUTPUT_PATH}")
    print(f"  - Content Index: {CONTENT_OUTPUT_PATH}")
    print(f"  - Warnings: {WARNINGS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
