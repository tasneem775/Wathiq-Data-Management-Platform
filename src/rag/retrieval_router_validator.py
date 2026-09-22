"""
Retrieval Router Validator — التحقق من صحة Retrieval Router بالكامل قبل إدخال
أي Embeddings أو ChromaDB.

لا يستخدم LLM ولا AI ولا LangChain ولا ChromaDB — فحوصات قائمة على مطابقة
بيانات مُحسوبة مباشرة من ملفات JSON الخام (مصدر مستقل عن Router نفسه) مقابل
مخرجات RetrievalRouter الفعلية.

مصادر القراءة فقط:
- data/knowledge_graph/dc_knowledge_graph.json
- data/rag_index/dc_rag_metadata_index.json
- data/rag_index/dc_rag_content_index.json
- src/rag/retrieval_router.py

الناتج:
- reports/retrieval_router_validation_report.txt (UTF-8)
"""

import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_GRAPH_PATH = PROJECT_ROOT / "data" / "knowledge_graph" / "dc_knowledge_graph.json"
METADATA_INDEX_PATH = PROJECT_ROOT / "data" / "rag_index" / "dc_rag_metadata_index.json"
CONTENT_INDEX_PATH = PROJECT_ROOT / "data" / "rag_index" / "dc_rag_content_index.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "retrieval_router_validation_report.txt"

sys.path.insert(0, str(PROJECT_ROOT))
from src.rag.retrieval_router import RetrievalRouter  # noqa: E402

RELEVANT_PAGE_ROLES = {
    "Official Maturity Reference",
    "Detailed Requirement Page",
    "Supporting Policy Page",
    "Summary Page",
}


def _normalize(text):
    if text is None:
        return ""
    return unicodedata.normalize("NFC", text).strip()


def _load_ground_truth():
    with open(KNOWLEDGE_GRAPH_PATH, encoding="utf-8") as f:
        nodes = json.load(f).get("nodes", [])
    with open(METADATA_INDEX_PATH, encoding="utf-8") as f:
        metadata_chunks = json.load(f)
    with open(CONTENT_INDEX_PATH, encoding="utf-8") as f:
        content_chunks = json.load(f)
    return nodes, metadata_chunks, content_chunks


class ValidationResult:
    def __init__(self, test_id, name):
        self.test_id = test_id
        self.name = name
        self.status = "PASS"
        self.details = []
        self.warnings = []

    def fail(self, message):
        self.status = "FAIL"
        self.details.append(message)

    def ok(self, message):
        self.details.append(message)

    def warn(self, message):
        self.warnings.append(message)


def test_evidence_routing(router, metadata_chunks, content_chunks):
    r = ValidationResult(1, "Evidence Routing Validation")
    code = "DC.M.6"

    expected_metadata = [c for c in metadata_chunks if c["evidence_code"] == code]
    expected_content = [c for c in content_chunks if c["evidence_code"] == code]

    bundle = router.route_by_evidence_code(code)

    if bundle["node"] is None:
        r.fail(f"Node لدليل {code} غير موجود")
    else:
        r.ok(f"Node لدليل {code} موجود")

    actual_metadata_count = len(bundle["metadata_chunks"])
    if actual_metadata_count == 8 == len(expected_metadata):
        r.ok(f"عدد Metadata Chunks = {actual_metadata_count} (متوقع: 8)")
    else:
        r.fail(
            f"عدد Metadata Chunks = {actual_metadata_count} (متوقع: 8، "
            f"من البيانات الخام: {len(expected_metadata)})"
        )

    actual_content_count = len(bundle["content_chunks"])
    if actual_content_count == 6 == len(expected_content):
        r.ok(f"عدد Content Chunks = {actual_content_count} (متوقع: 6)")
    else:
        r.fail(
            f"عدد Content Chunks = {actual_content_count} (متوقع: 6، "
            f"من البيانات الخام: {len(expected_content)})"
        )

    return r


def test_mq_routing(router, nodes):
    r = ValidationResult(2, "MQ Routing Validation")
    mq_id = "DC.MQ.2"

    expected_count = len([n for n in nodes if n["mq_id"] == mq_id])
    actual = router.route_by_mq(mq_id)

    if len(actual) == 12 == expected_count:
        r.ok(f"عدد الأدلة لـ {mq_id} = {len(actual)} (متوقع: 12)")
    else:
        r.fail(
            f"عدد الأدلة لـ {mq_id} = {len(actual)} (متوقع: 12، "
            f"من البيانات الخام: {expected_count})"
        )

    return r


def test_level_routing(router, nodes):
    r = ValidationResult(3, "Level Routing Validation")
    level_number = 2
    expected_codes = sorted(["DC.C.1.1", "DC.C.2.1", "DC.M.6", "DC.M.11"])

    raw_codes = sorted([n["evidence_code"] for n in nodes if n["level"]["number"] == level_number])
    bundles = router.route_by_level(level_number)
    actual_codes = sorted([b["node"]["evidence_code"] for b in bundles])

    if actual_codes == expected_codes == raw_codes:
        r.ok(f"الأدلة المُعادة للمستوى {level_number}: {actual_codes}")
    else:
        r.fail(
            f"الأدلة المُعادة: {actual_codes} | المتوقع: {expected_codes} | "
            f"من البيانات الخام: {raw_codes}"
        )

    return r


def test_document_routing(router, metadata_chunks, content_chunks):
    r = ValidationResult(4, "Document Routing Validation")
    document_name = "المؤشر الوطني للبيانات"
    doc_key = _normalize(document_name)

    expected_metadata = [c for c in metadata_chunks if _normalize(c.get("source_document")) == doc_key]
    expected_content = [c for c in content_chunks if _normalize(c.get("source_document")) == doc_key]

    result = router.route_by_document(document_name)

    if len(result["metadata_chunks"]) == 16 == len(expected_metadata):
        r.ok(f"عدد Metadata Chunks = {len(result['metadata_chunks'])} (متوقع: 16)")
    else:
        r.fail(
            f"عدد Metadata Chunks = {len(result['metadata_chunks'])} (متوقع: 16، "
            f"من البيانات الخام: {len(expected_metadata)})"
        )

    if len(result["content_chunks"]) == 16 == len(expected_content):
        r.ok(f"عدد Content Chunks = {len(result['content_chunks'])} (متوقع: 16)")
    else:
        r.fail(
            f"عدد Content Chunks = {len(result['content_chunks'])} (متوقع: 16، "
            f"من البيانات الخام: {len(expected_content)})"
        )

    return r


def test_page_role_routing(router, metadata_chunks, content_chunks):
    r = ValidationResult(5, "Page Role Validation")
    page_role = "Detailed Requirement Page"

    expected_content_ids = sorted(
        c["chunk_id"] for c in content_chunks if c.get("page_role") == page_role
    )
    metadata_chunk_ids = {c["chunk_id"] for c in metadata_chunks}

    actual = router.route_by_page_role(page_role)
    actual_ids = sorted(c["chunk_id"] for c in actual)

    if actual_ids != expected_content_ids:
        r.fail(
            f"chunk_ids المُعادة لا تطابق البيانات الخام | "
            f"معاد: {len(actual_ids)} | متوقع: {len(expected_content_ids)}"
        )
        return r
    r.ok(f"عدد Content Chunks المُعادة = {len(actual_ids)} ويطابق البيانات الخام")

    contaminated = [chunk_id for chunk_id in actual_ids if chunk_id in metadata_chunk_ids]
    if contaminated:
        r.fail(f"تم العثور على Metadata Chunks ضمن نتيجة route_by_page_role: {contaminated}")
    else:
        r.ok("لا يوجد أي Metadata Chunk ضمن النتيجة")

    non_content_schema = [c["chunk_id"] for c in actual if "source_path" not in c]
    if non_content_schema:
        r.fail(f"عناصر لا تطابق بنية Content Chunk (بدون source_path): {non_content_schema}")
    else:
        r.ok("كل العناصر المُعادة تطابق بنية Content Chunk (تحتوي source_path)")

    return r


def test_retrieval_plan(router):
    r = ValidationResult(6, "Retrieval Plan Validation")
    query = "ما المطلوب في DC.M.6؟"
    plan = router.build_retrieval_plan(query)

    checks = [
        ("strategy", plan.get("strategy"), "evidence_code"),
        ("target", plan.get("target"), "DC.M.6"),
        ("metadata_chunks", plan.get("metadata_chunks"), 8),
        ("content_chunks", plan.get("content_chunks"), 6),
    ]

    for field, actual_value, expected_value in checks:
        if actual_value == expected_value:
            r.ok(f"{field} = {actual_value} (متوقع: {expected_value})")
        else:
            r.fail(f"{field} = {actual_value} (متوقع: {expected_value})")

    return r, plan


def test_consistency(router, plan):
    r = ValidationResult(7, "Consistency Validation")
    target_code = plan.get("target")

    if target_code is None:
        r.warn("لا يوجد target في Retrieval Plan لتنفيذ فحص الاتساق عليه")
        return r

    bundle = router.route_by_evidence_code(target_code)
    metadata_chunks = bundle["metadata_chunks"]
    content_chunks = bundle["content_chunks"]

    content_index = {
        (c["evidence_code"], _normalize(c.get("source_document")), c.get("page_number"), c.get("page_role"))
        for c in content_chunks
    }

    checked = 0
    for m_chunk in metadata_chunks:
        page_role = m_chunk.get("page_role")
        if page_role not in RELEVANT_PAGE_ROLES:
            continue
        checked += 1
        key = (
            m_chunk["evidence_code"],
            _normalize(m_chunk.get("source_document")),
            m_chunk.get("page_number"),
            page_role,
        )
        if key not in content_index:
            r.warn(
                f"Metadata Chunk {m_chunk['chunk_id']} (page_role={page_role}, "
                f"source_document={m_chunk.get('source_document')}, page_number={m_chunk.get('page_number')}) "
                f"بلا Content Chunk مطابق."
            )

    if not r.warnings:
        r.ok(f"تم فحص {checked} Metadata Chunk ذات page_role مؤهل — كلها لها Content Chunk مطابق")
    else:
        r.ok(f"تم فحص {checked} Metadata Chunk ذات page_role مؤهل — {len(r.warnings)} بلا مطابقة (انظر Warnings)")

    return r


def test_duplicates(content_chunks):
    r = ValidationResult(8, "Duplicate Validation")

    keys = [
        (c["evidence_code"], _normalize(c.get("source_document")), c.get("page_number"))
        for c in content_chunks
    ]
    counts = Counter(keys)
    duplicates = {k: v for k, v in counts.items() if v > 1}

    if duplicates:
        r.fail(f"تم العثور على {len(duplicates)} مفتاح مكرر (evidence_code, source_document, page_number)")
        for key, count in duplicates.items():
            r.fail(f"  مكرر: {key} — عدد التكرارات: {count}")
    else:
        r.ok(f"لا توجد Content Chunks مكررة من أصل {len(content_chunks)} chunk")

    return r


def build_report_text(results):
    lines = []
    lines.append("=" * 60)
    lines.append("تقرير التحقق من Retrieval Router")
    lines.append("Retrieval Router Validation Report")
    lines.append("=" * 60)
    lines.append("")

    pass_count = sum(1 for r in results if r.status == "PASS")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    warnings_count = sum(len(r.warnings) for r in results)
    overall_result = "FAIL" if fail_count > 0 else "PASS"

    lines.append(f"عدد الاختبارات: {len(results)}")
    lines.append(f"عدد PASS: {pass_count}")
    lines.append(f"عدد FAIL: {fail_count}")
    lines.append(f"عدد Warnings: {warnings_count}")
    lines.append(f"النتيجة النهائية: {overall_result}")
    lines.append("")
    lines.append("=" * 60)

    for r in results:
        lines.append("")
        lines.append("-" * 60)
        lines.append(f"اختبار {r.test_id}: {r.name}")
        lines.append(f"الحالة: [{r.status}]")
        lines.append("-" * 60)
        for detail in r.details:
            lines.append(f"  - {detail}")
        for warning in r.warnings:
            lines.append(f"  [WARNING] {warning}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines), pass_count, fail_count, warnings_count, overall_result


def main():
    nodes, metadata_chunks, content_chunks = _load_ground_truth()
    router = RetrievalRouter()

    results = []
    results.append(test_evidence_routing(router, metadata_chunks, content_chunks))
    results.append(test_mq_routing(router, nodes))
    results.append(test_level_routing(router, nodes))
    results.append(test_document_routing(router, metadata_chunks, content_chunks))
    results.append(test_page_role_routing(router, metadata_chunks, content_chunks))

    plan_result, plan = test_retrieval_plan(router)
    results.append(plan_result)

    results.append(test_consistency(router, plan))
    results.append(test_duplicates(content_chunks))

    report_text, pass_count, fail_count, warnings_count, overall_result = build_report_text(results)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"عدد PASS: {pass_count}")
    print(f"عدد FAIL: {fail_count}")
    print(f"عدد Warnings: {warnings_count}")
    print(f"Overall Result: {overall_result}")


if __name__ == "__main__":
    main()
