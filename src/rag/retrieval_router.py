"""
Retrieval Router — Hybrid Retrieval Architecture, المرحلة الأولى.

يقرر ما الذي يجب استرجاعه (أي Evidence / أي Chunks) قبل اللجوء لأي Vector Search.
لا يستخدم LLM ولا LangChain ولا ChromaDB ولا Embeddings — توجيه قائم على قواعد
ومطابقة نصية/بنيوية على البيانات المُفهرسة مسبقاً فقط.

مصادر البيانات (قراءة فقط):
- data/knowledge_graph/dc_knowledge_graph.json
- data/rag_index/dc_rag_metadata_index.json
- data/rag_index/dc_rag_content_index.json
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
KNOWLEDGE_GRAPH_PATH = PROJECT_ROOT / "data" / "knowledge_graph" / "dc_knowledge_graph.json"
METADATA_INDEX_PATH = PROJECT_ROOT / "data" / "rag_index" / "dc_rag_metadata_index.json"
CONTENT_INDEX_PATH = PROJECT_ROOT / "data" / "rag_index" / "dc_rag_content_index.json"

EVIDENCE_CODE_PATTERN = re.compile(r"\b[A-Za-z]{2,4}\.(?:M|C)\.\d+(?:\.\d+)?\b")
MQ_ID_PATTERN = re.compile(r"\b[A-Za-z]{2,4}\.MQ\.\d+\b", re.IGNORECASE)
LEVEL_PATTERN = re.compile(r"(?:level|مستوى)\D{0,3}(\d+)", re.IGNORECASE)


def _normalize(text):
    if text is None:
        return ""
    return unicodedata.normalize("NFC", text).strip()


class RetrievalRouter:
    """Router قائم على قواعد يربط الاستعلامات بأدلة/Chunks محددة سلفاً."""

    def __init__(self,
                 knowledge_graph_path=KNOWLEDGE_GRAPH_PATH,
                 metadata_index_path=METADATA_INDEX_PATH,
                 content_index_path=CONTENT_INDEX_PATH):
        with open(knowledge_graph_path, encoding="utf-8") as f:
            self.nodes = json.load(f).get("nodes", [])
        with open(metadata_index_path, encoding="utf-8") as f:
            self.metadata_chunks = json.load(f)
        with open(content_index_path, encoding="utf-8") as f:
            self.content_chunks = json.load(f)

        self._build_indices()

    def _build_indices(self):
        self.nodes_by_code = {}
        self.nodes_by_mq = {}
        self.nodes_by_level = {}
        for node in self.nodes:
            self.nodes_by_code[node["evidence_code"]] = node
            self.nodes_by_mq.setdefault(node["mq_id"], []).append(node)
            self.nodes_by_level.setdefault(node["level"]["number"], []).append(node)

        self.metadata_by_code = {}
        self.metadata_by_document = {}
        for chunk in self.metadata_chunks:
            self.metadata_by_code.setdefault(chunk["evidence_code"], []).append(chunk)
            doc_key = _normalize(chunk.get("source_document"))
            if doc_key:
                self.metadata_by_document.setdefault(doc_key, []).append(chunk)

        self.content_by_code = {}
        self.content_by_document = {}
        self.content_by_page_role = {}
        for chunk in self.content_chunks:
            self.content_by_code.setdefault(chunk["evidence_code"], []).append(chunk)
            doc_key = _normalize(chunk.get("source_document"))
            if doc_key:
                self.content_by_document.setdefault(doc_key, []).append(chunk)
            role_key = chunk.get("page_role")
            if role_key:
                self.content_by_page_role.setdefault(role_key, []).append(chunk)

    # -- helpers ------------------------------------------------------

    def _bundle(self, node):
        code = node["evidence_code"]
        return {
            "node": node,
            "metadata_chunks": self.metadata_by_code.get(code, []),
            "content_chunks": self.content_by_code.get(code, []),
        }

    # -- routing functions ---------------------------------------------

    def route_by_evidence_code(self, evidence_code):
        node = self.nodes_by_code.get(evidence_code)
        if node is None:
            return {"node": None, "metadata_chunks": [], "content_chunks": []}
        return self._bundle(node)

    def route_by_mq(self, mq_id):
        return [self._bundle(node) for node in self.nodes_by_mq.get(mq_id, [])]

    def route_by_level(self, level_number):
        return [self._bundle(node) for node in self.nodes_by_level.get(level_number, [])]

    def route_by_document(self, document_name):
        doc_key = _normalize(document_name)
        return {
            "metadata_chunks": self.metadata_by_document.get(doc_key, []),
            "content_chunks": self.content_by_document.get(doc_key, []),
        }

    def route_by_page_role(self, page_role):
        return self.content_by_page_role.get(page_role, [])

    # -- query planning --------------------------------------------------

    def build_retrieval_plan(self, query):
        code_match = EVIDENCE_CODE_PATTERN.search(query)
        if code_match:
            code = code_match.group(0).upper()
            if code in self.nodes_by_code:
                bundle = self.route_by_evidence_code(code)
                documents = sorted({
                    _normalize(c.get("source_document"))
                    for c in bundle["metadata_chunks"] + bundle["content_chunks"]
                    if c.get("source_document")
                })
                return {
                    "strategy": "evidence_code",
                    "target": code,
                    "metadata_chunks": len(bundle["metadata_chunks"]),
                    "content_chunks": len(bundle["content_chunks"]),
                    "documents": documents,
                }

        mq_match = MQ_ID_PATTERN.search(query)
        if mq_match:
            mq_id = mq_match.group(0).upper()
            if mq_id in self.nodes_by_mq:
                bundles = self.route_by_mq(mq_id)
                metadata_count = sum(len(b["metadata_chunks"]) for b in bundles)
                content_count = sum(len(b["content_chunks"]) for b in bundles)
                documents = sorted({
                    _normalize(c.get("source_document"))
                    for b in bundles
                    for c in b["metadata_chunks"] + b["content_chunks"]
                    if c.get("source_document")
                })
                return {
                    "strategy": "mq",
                    "target": mq_id,
                    "metadata_chunks": metadata_count,
                    "content_chunks": content_count,
                    "documents": documents,
                }

        level_match = LEVEL_PATTERN.search(query)
        if level_match:
            level_number = int(level_match.group(1))
            if level_number in self.nodes_by_level:
                bundles = self.route_by_level(level_number)
                metadata_count = sum(len(b["metadata_chunks"]) for b in bundles)
                content_count = sum(len(b["content_chunks"]) for b in bundles)
                documents = sorted({
                    _normalize(c.get("source_document"))
                    for b in bundles
                    for c in b["metadata_chunks"] + b["content_chunks"]
                    if c.get("source_document")
                })
                return {
                    "strategy": "level",
                    "target": level_number,
                    "metadata_chunks": metadata_count,
                    "content_chunks": content_count,
                    "documents": documents,
                }

        return {
            "strategy": "unresolved",
            "target": None,
            "metadata_chunks": 0,
            "content_chunks": 0,
            "documents": [],
        }


_default_router = None


def _get_default_router():
    global _default_router
    if _default_router is None:
        _default_router = RetrievalRouter()
    return _default_router


def route_by_evidence_code(evidence_code):
    return _get_default_router().route_by_evidence_code(evidence_code)


def route_by_mq(mq_id):
    return _get_default_router().route_by_mq(mq_id)


def route_by_level(level_number):
    return _get_default_router().route_by_level(level_number)


def route_by_document(document_name):
    return _get_default_router().route_by_document(document_name)


def route_by_page_role(page_role):
    return _get_default_router().route_by_page_role(page_role)


def build_retrieval_plan(query):
    return _get_default_router().build_retrieval_plan(query)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _print_bundle(label, bundle):
    node = bundle["node"]
    print(f"\n{label}")
    if node is None:
        print("  node: غير موجود")
        return
    print(f"  evidence_code: {node['evidence_code']}")
    print(f"  evidence_name: {node['evidence_name']}")
    print(f"  mq_id: {node['mq_id']} | level: {node['level']['number']} ({node['level']['name']})")
    print(f"  metadata_chunks: {len(bundle['metadata_chunks'])}")
    for c in bundle["metadata_chunks"]:
        print(f"    - {c['chunk_id']}")
    print(f"  content_chunks: {len(bundle['content_chunks'])}")
    for c in bundle["content_chunks"]:
        print(f"    - {c['chunk_id']} ({len(c['text'])} حرف)")


def _print_bundles(label, bundles):
    print(f"\n{label} — عدد الأدلة: {len(bundles)}")
    for bundle in bundles:
        node = bundle["node"]
        print(
            f"  - {node['evidence_code']} | {node['evidence_name']} "
            f"| metadata={len(bundle['metadata_chunks'])} content={len(bundle['content_chunks'])}"
        )


def main():
    router = RetrievalRouter()

    _print_bundle(
        'route_by_evidence_code("DC.M.6")',
        router.route_by_evidence_code("DC.M.6"),
    )

    _print_bundles(
        'route_by_mq("DC.MQ.2")',
        router.route_by_mq("DC.MQ.2"),
    )

    _print_bundles(
        "route_by_level(2)",
        router.route_by_level(2),
    )

    doc_result = router.route_by_document("المؤشر الوطني للبيانات")
    print('\nroute_by_document("المؤشر الوطني للبيانات")')
    print(f"  metadata_chunks: {len(doc_result['metadata_chunks'])}")
    print(f"  content_chunks: {len(doc_result['content_chunks'])}")

    plan = router.build_retrieval_plan("ما المطلوب في DC.M.6؟")
    print('\nbuild_retrieval_plan("ما المطلوب في DC.M.6؟")')
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
