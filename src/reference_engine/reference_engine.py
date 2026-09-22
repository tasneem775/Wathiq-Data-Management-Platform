"""Knowledge Reference Discovery Engine.

Discovers, for each Evidence in the Knowledge Catalog, every official
reference PDF (registered in knowledge_base/knowledge_sources.json) that
contains a literal match of its evidence_code or evidence_name.

Every registered document is checked for every Evidence, and every page of
every document is checked — a match on one page, or in one document, never
stops the search elsewhere, since the same Evidence may legitimately appear
several times across (and within) several official references.

Evidence Name matches are additionally screened against a cross-domain
false-positive rule: an Evidence Name can coincidentally reuse wording that
also appears in an unrelated domain's material (e.g. "سجل البيانات" inside an
Open Data "سجل البيانات المفتوحة" passage). Such matches are excluded rather
than reported, and are listed separately at the end of the report.

No AI, embeddings, semantic search, or OCR is used — matching is a plain
substring search over text extracted with PyMuPDF.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_CATALOG_PATH = (
    PROJECT_ROOT / "data" / "knowledge_catalog" / "dc_knowledge_catalog.json"
)
KNOWLEDGE_SOURCES_PATH = PROJECT_ROOT / "knowledge_base" / "knowledge_sources.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "reference_engine_report.txt"

CONTEXT_RADIUS = 150

# If an Evidence Name match and an Evidence Code match land on the same page
# within this many characters of each other, the name match is treated as
# the same textual spot as the code match (not a second, independent
# reference) and is not recorded separately.
NAME_CODE_PROXIMITY = CONTEXT_RADIUS * 2

MATURITY_LEVEL_NAMES = ("البناء", "التعريف", "التفعيل", "التمكن", "الريادة")

DETAILED_REQUIREMENT_PHRASES = (
    "معايير القبول",
    "معايير قبول",
    "يجب على الجهة",
    "على الجهة",
    "كحد أدنى",
    "ينبغي أن يشمل",
    "يجب أن يتضمن",
    "يجب أن تشمل",
    "يجب أن ترفق",
    "يجب إرفاق",
    "الأدلة الداعمة",
    "الوثائق والأدلة الداعمة",
)

SUPPORTING_POLICY_KEYWORDS = ("سياسة", "ضوابط", "نظام")

OFFICIAL_MATURITY_DOCUMENT_NAME = "المؤشر الوطني للبيانات"

# Matches domain-code-like tokens such as "DC.M.1", "DC.C.5.1", "OD.5.1",
# "DQ.MQ.1" - a short run of uppercase Latin letters (the domain prefix)
# followed by a dot and a numeric code. Used both to spot "another domain's
# code" inside a match's context, and to detect summary pages that mention
# several distinct evidence codes at once.
DOMAIN_CODE_PATTERN = re.compile(r"([A-Z]{2,6})\.(?:[A-Z]{1,3}\.)?\d+(?:\.\d+)*")


@dataclass
class PageEntry:
    """One page of a PDF held in the in-memory page index."""

    page_number: int
    extracted_text: str


@dataclass
class MatchResult:
    """A single Evidence-to-reference match found during the search."""

    evidence_code: str
    evidence_name: str
    document_name: str
    page_number: int
    matched_by: str
    confidence: float
    matched_text: str
    context: str
    page_role: str


@dataclass
class ExcludedMatch:
    """A candidate match rejected by the cross-domain false-positive rule."""

    evidence_code: str
    evidence_name: str
    document_name: str
    page_number: int
    matched_by: str
    matched_text: str
    reason: str
    context: str


def load_knowledge_catalog() -> list[dict[str, Any]]:
    """Read the Knowledge Catalog and return its list of Evidence records."""
    with KNOWLEDGE_CATALOG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_knowledge_sources() -> list[dict[str, Any]]:
    """Read the registry of official knowledge sources (PDF references)."""
    with KNOWLEDGE_SOURCES_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data["knowledge_sources"]


def load_source_types(sources: list[dict[str, Any]]) -> dict[str, str]:
    """Map each source_name to its source_type, as registered in the sources file."""
    return {source["source_name"]: source["source_type"] for source in sources}


def build_page_index(pdf_path: Path) -> list[PageEntry]:
    """Open a PDF once and extract its text into an in-memory page index."""
    pages: list[PageEntry] = []
    document = fitz.open(pdf_path)
    try:
        for page_number in range(document.page_count):
            page = document.load_page(page_number)
            pages.append(
                PageEntry(page_number=page_number + 1, extracted_text=page.get_text())
            )
    finally:
        document.close()
    return pages


def resolve_source_path(file_path: str) -> Path | None:
    """Resolve a registered source file_path to an existing file on disk.

    Falls back to a Unicode-normalized filename comparison within the same
    directory, since Arabic filenames can be stored in different
    normalization forms (composed vs. decomposed) than the registry entry.
    """
    direct_path = PROJECT_ROOT / file_path
    if direct_path.exists():
        return direct_path

    relative_path = Path(file_path)
    parent_directory = PROJECT_ROOT / relative_path.parent
    if not parent_directory.exists():
        return None

    target_name = unicodedata.normalize("NFC", relative_path.name)
    for entry in parent_directory.iterdir():
        if entry.is_file() and unicodedata.normalize("NFC", entry.name) == target_name:
            return entry
    return None


def build_document_indexes(
    sources: list[dict[str, Any]],
) -> dict[str, list[PageEntry]]:
    """Build the in-memory page index for every registered knowledge source."""
    indexes: dict[str, list[PageEntry]] = {}
    for source in sources:
        pdf_path = resolve_source_path(source["file_path"])
        if pdf_path is None:
            continue
        indexes[source["source_name"]] = build_page_index(pdf_path)
    return indexes


def extract_context(text: str, match_start: int, match_end: int) -> str:
    """Return up to 300 characters of text centered on the match location."""
    start = max(0, match_start - CONTEXT_RADIUS)
    end = min(len(text), match_end + CONTEXT_RADIUS)
    return text[start:end].strip()


def find_code_occurrences(text: str, code: str) -> list[tuple[int, int]]:
    """Find every standalone occurrence of an Evidence Code in a page's text.

    A plain substring search for a code like "DC.M.1" would also match
    inside a longer code such as "DC.M.10" or "DC.M.11". A hit is only kept
    when it is not immediately preceded by an alphanumeric character and not
    immediately followed by a digit or a dot - both of which would mean the
    hit is merely a prefix of a different, longer code.
    """
    if not code:
        return []
    occurrences: list[tuple[int, int]] = []
    start = 0
    while True:
        index = text.find(code, start)
        if index == -1:
            break
        end = index + len(code)
        before_char = text[index - 1] if index > 0 else ""
        after_char = text[end] if end < len(text) else ""
        if not before_char.isalnum() and after_char not in "0123456789.":
            occurrences.append((index, end))
        start = index + 1
    return occurrences


def find_name_occurrences(text: str, name: str) -> list[tuple[int, int]]:
    """Find every non-overlapping occurrence of an Evidence Name in a page's text."""
    if not name:
        return []
    occurrences: list[tuple[int, int]] = []
    start = 0
    while True:
        index = text.find(name, start)
        if index == -1:
            break
        occurrences.append((index, index + len(name)))
        start = index + len(name)
    return occurrences


def get_domain_code(evidence: dict[str, Any]) -> str:
    """Return the Evidence's domain code, from domain_code or from evidence_code."""
    domain_code = evidence.get("domain_code")
    if domain_code:
        return domain_code
    return evidence["evidence_code"].split(".")[0]


def find_conflicting_domain_code(context: str, own_domain_code: str) -> str | None:
    """Return the first code belonging to a different domain found in a context."""
    for match in DOMAIN_CODE_PATTERN.finditer(context):
        if match.group(1) != own_domain_code:
            return match.group(0)
    return None


def has_own_domain_markers(
    context: str,
    own_domain_code: str,
    own_evidence_code: str,
    own_mq_id: str,
    own_domain_name_ar: str,
) -> bool:
    """Whether the context still anchors an Evidence Name match to its own domain."""
    if own_domain_code and own_domain_code in context:
        return True
    if own_evidence_code and own_evidence_code in context:
        return True
    if own_mq_id and own_mq_id in context:
        return True
    if own_domain_name_ar and own_domain_name_ar in context:
        return True
    return False


def classify_page_role(
    page_text: str,
    context: str,
    matched_by: str,
    source_type: str,
    document_name: str,
) -> str:
    """Classify the role a page plays for a given match.

    Checked in order. A page that spells out a detailed acceptance
    requirement ("يجب على الجهة", "كحد أدنى", ...) is a Detailed
    Requirement Page even when it also happens to mention several evidence
    codes or maturity levels in passing - the presence of an actual
    requirement is what matters, not how many codes surround it. Only once
    that is ruled out do we fall back to treating a multi-code / multi-level
    page as a plain Summary Page.
    """
    if any(phrase in context for phrase in DETAILED_REQUIREMENT_PHRASES) or any(
        phrase in page_text for phrase in DETAILED_REQUIREMENT_PHRASES
    ):
        return "Detailed Requirement Page"

    if (
        source_type == "Supporting Official Reference"
        and matched_by == "Evidence Name"
        and any(keyword in context for keyword in SUPPORTING_POLICY_KEYWORDS)
    ):
        return "Supporting Policy Page"

    if source_type == "Official Reference" or document_name == OFFICIAL_MATURITY_DOCUMENT_NAME:
        return "Official Maturity Reference"

    distinct_codes = {match.group(0) for match in DOMAIN_CODE_PATTERN.finditer(page_text)}
    distinct_levels = {level for level in MATURITY_LEVEL_NAMES if level in page_text}
    if len(distinct_codes) > 1 or len(distinct_levels) > 1:
        return "Summary Page"

    if source_type == "Training Reference":
        return "Training Reference Page"

    return "Unknown"


def deduplicate_matches(matches: list[MatchResult]) -> list[MatchResult]:
    """Drop matches that repeat the same document, page, method, and text."""
    seen: set[tuple[str, int, str, str]] = set()
    unique: list[MatchResult] = []
    for match in matches:
        key = (match.document_name, match.page_number, match.matched_by, match.matched_text)
        if key in seen:
            continue
        seen.add(key)
        unique.append(match)
    return unique


def deduplicate_excluded(excluded: list[ExcludedMatch]) -> list[ExcludedMatch]:
    """Drop excluded entries that repeat the same document, page, method, and text."""
    seen: set[tuple[str, int, str, str]] = set()
    unique: list[ExcludedMatch] = []
    for item in excluded:
        key = (item.document_name, item.page_number, item.matched_by, item.matched_text)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def find_references_for_evidence(
    evidence: dict[str, Any],
    document_indexes: dict[str, list[PageEntry]],
    source_types: dict[str, str],
) -> tuple[list[MatchResult], list[ExcludedMatch]]:
    """Search every registered document, every page, for one Evidence.

    Within each document, every page is checked for both Evidence Code and
    Evidence Name independently, and a hit does not stop the search on
    later pages or in later documents. An Evidence Name hit that lands on
    the same page and close to an already-found Evidence Code hit is
    treated as the same textual spot (not a second reference). Remaining
    Evidence Name hits are screened by the cross-domain rule before being
    accepted: if their context clearly belongs to a different domain's code
    and carries no marker tying it back to this Evidence's own domain, code,
    or MQ, the hit is rejected and recorded as excluded instead.
    """
    evidence_code = evidence["evidence_code"]
    evidence_name = evidence["evidence_name"]
    own_mq_id = evidence["mq_id"]
    own_domain_code = get_domain_code(evidence)
    own_domain_name_ar = evidence.get("domain_name_ar", "")

    matches: list[MatchResult] = []
    excluded: list[ExcludedMatch] = []

    for document_name, pages in document_indexes.items():
        source_type = source_types.get(document_name, "")

        code_hit_by_page: dict[int, tuple[int, int, str]] = {}
        for page in pages:
            hits = find_code_occurrences(page.extracted_text, evidence_code)
            if hits:
                start, end = hits[0]
                code_hit_by_page[page.page_number] = (start, end, page.extracted_text)

        name_hit_by_page: dict[int, tuple[int, int, str]] = {}
        for page in pages:
            hits = find_name_occurrences(page.extracted_text, evidence_name)
            if not hits:
                continue
            code_hit = code_hit_by_page.get(page.page_number)
            for start, end in hits:
                if code_hit is not None and abs(start - code_hit[0]) < NAME_CODE_PROXIMITY:
                    continue
                name_hit_by_page[page.page_number] = (start, end, page.extracted_text)
                break

        for page_number in sorted(set(code_hit_by_page) | set(name_hit_by_page)):
            if page_number in code_hit_by_page:
                start, end, text = code_hit_by_page[page_number]
                context = extract_context(text, start, end)
                page_role = classify_page_role(
                    text, context, "Evidence Code", source_type, document_name
                )
                matches.append(
                    MatchResult(
                        evidence_code=evidence_code,
                        evidence_name=evidence_name,
                        document_name=document_name,
                        page_number=page_number,
                        matched_by="Evidence Code",
                        confidence=1.0,
                        matched_text=text[start:end],
                        context=context,
                        page_role=page_role,
                    )
                )

            if page_number in name_hit_by_page:
                start, end, text = name_hit_by_page[page_number]
                context = extract_context(text, start, end)
                matched_text = text[start:end]

                foreign_code = find_conflicting_domain_code(context, own_domain_code)
                if foreign_code and not has_own_domain_markers(
                    context, own_domain_code, evidence_code, own_mq_id, own_domain_name_ar
                ):
                    excluded.append(
                        ExcludedMatch(
                            evidence_code=evidence_code,
                            evidence_name=evidence_name,
                            document_name=document_name,
                            page_number=page_number,
                            matched_by="Evidence Name",
                            matched_text=matched_text,
                            reason=(
                                f"السياق يحتوي على كود من مجال مختلف ({foreign_code}) "
                                f"ولا يحتوي على مجال {own_domain_code} أو نفس الكود "
                                f"({evidence_code}) أو نفس السؤال ({own_mq_id})"
                            ),
                            context=context,
                        )
                    )
                    continue

                page_role = classify_page_role(
                    text, context, "Evidence Name", source_type, document_name
                )
                matches.append(
                    MatchResult(
                        evidence_code=evidence_code,
                        evidence_name=evidence_name,
                        document_name=document_name,
                        page_number=page_number,
                        matched_by="Evidence Name",
                        confidence=0.9,
                        matched_text=matched_text,
                        context=context,
                        page_role=page_role,
                    )
                )

    return deduplicate_matches(matches), deduplicate_excluded(excluded)


def evidence_sort_key(evidence: dict[str, Any]) -> tuple[str, int, str]:
    """Sort key for the report: by MQ, then Level, then Evidence Code."""
    return (evidence["mq_id"], evidence["level_number"], evidence["evidence_code"])


PAGE_ROLE_ORDER = (
    "Summary Page",
    "Detailed Requirement Page",
    "Official Maturity Reference",
    "Training Reference Page",
    "Supporting Policy Page",
    "Unknown",
)


def count_page_roles(matches: list[MatchResult]) -> dict[str, int]:
    """Tally how many of an Evidence's matches fall under each page_role."""
    counts = {role: 0 for role in PAGE_ROLE_ORDER}
    for match in matches:
        counts[match.page_role] = counts.get(match.page_role, 0) + 1
    return counts


def build_report(
    scanned_pdf_count: int,
    evidence_count: int,
    evidence_matches: list[tuple[dict[str, Any], list[MatchResult]]],
    unmatched: list[dict[str, Any]],
    source_types: dict[str, str],
    excluded_matches: list[ExcludedMatch],
) -> str:
    """Render a human-readable Arabic review report of the discovery results."""
    total_matches = sum(len(matches) for _, matches in evidence_matches)
    lines: list[str] = []

    lines.append("=" * 50)
    lines.append("تقرير محرك اكتشاف المراجع")
    lines.append("Knowledge Reference Discovery Engine")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"عدد ملفات PDF التي تم فحصها: {scanned_pdf_count}")
    lines.append("")
    lines.append(f"عدد الأدلة: {evidence_count}")
    lines.append("")
    lines.append(f"عدد المطابقات: {total_matches}")
    lines.append("")
    lines.append(f"عدد الأدلة التي لم يتم العثور عليها: {len(unmatched)}")
    lines.append("")
    lines.append(f"عدد المطابقات المستبعدة: {len(excluded_matches)}")
    lines.append("")
    lines.append("=" * 50)
    lines.append("")

    for evidence, matches in evidence_matches:
        role_counts = count_page_roles(matches)

        lines.append("-" * 50)
        lines.append("رمز الدليل:")
        lines.append(evidence["evidence_code"])
        lines.append("")
        lines.append("اسم الدليل:")
        lines.append(evidence["evidence_name"])
        lines.append("")
        lines.append("السؤال:")
        lines.append(evidence["mq_id"])
        lines.append("")
        lines.append("المستوى:")
        lines.append(evidence["level_name"])
        lines.append("")
        lines.append("عدد المراجع المكتشفة:")
        lines.append(str(len(matches)))
        lines.append("")
        lines.append("عدد Summary Page:")
        lines.append(str(role_counts["Summary Page"]))
        lines.append("")
        lines.append("عدد Detailed Requirement Page:")
        lines.append(str(role_counts["Detailed Requirement Page"]))
        lines.append("")
        lines.append("عدد Official Maturity Reference:")
        lines.append(str(role_counts["Official Maturity Reference"]))
        lines.append("")
        lines.append("عدد Training Reference Page:")
        lines.append(str(role_counts["Training Reference Page"]))
        lines.append("")
        lines.append("عدد Supporting Policy Page:")
        lines.append(str(role_counts["Supporting Policy Page"]))
        lines.append("")
        lines.append("عدد Unknown:")
        lines.append(str(role_counts["Unknown"]))
        lines.append("-" * 50)
        lines.append("")

        for index, match in enumerate(matches, start=1):
            lines.append(f"مرجع رقم ({index})")
            lines.append("")
            lines.append("اسم الملف:")
            lines.append(match.document_name)
            lines.append("")
            lines.append("نوع المرجع:")
            lines.append(source_types.get(match.document_name, ""))
            lines.append("")
            lines.append("رقم الصفحة:")
            lines.append(str(match.page_number))
            lines.append("")
            lines.append("طريقة المطابقة:")
            lines.append(match.matched_by)
            lines.append("")
            lines.append("درجة الثقة:")
            lines.append(str(match.confidence))
            lines.append("")
            lines.append("page_role:")
            lines.append(match.page_role)
            lines.append("")
            lines.append("النص المطابق:")
            lines.append(match.matched_text)
            lines.append("")
            lines.append("سياق المطابقة:")
            lines.append(match.context)
            lines.append("")
            lines.append("-" * 50)
            lines.append("")

    lines.append("=" * 50)
    lines.append("أدلة بدون أي مرجع")
    lines.append("=" * 50)
    lines.append("")
    for evidence in unmatched:
        lines.append(f"- {evidence['evidence_code']}")
        lines.append(f"- {evidence['evidence_name']}")
        lines.append("")

    lines.append("=" * 50)
    lines.append("مطابقات مستبعدة")
    lines.append("=" * 50)
    lines.append("")
    for excluded in excluded_matches:
        lines.append("-" * 50)
        lines.append("evidence_code:")
        lines.append(excluded.evidence_code)
        lines.append("")
        lines.append("evidence_name:")
        lines.append(excluded.evidence_name)
        lines.append("")
        lines.append("document_name:")
        lines.append(excluded.document_name)
        lines.append("")
        lines.append("page_number:")
        lines.append(str(excluded.page_number))
        lines.append("")
        lines.append("matched_by:")
        lines.append(excluded.matched_by)
        lines.append("")
        lines.append("matched_text:")
        lines.append(excluded.matched_text)
        lines.append("")
        lines.append("سبب الاستبعاد:")
        lines.append(excluded.reason)
        lines.append("")
        lines.append("جزء من السياق:")
        lines.append(excluded.context[:200])
        lines.append("")
        lines.append("-" * 50)
        lines.append("")

    return "\n".join(lines) + "\n"


def run() -> None:
    """Entry point: load inputs, search every document, and save the report."""
    catalog = load_knowledge_catalog()
    sources = load_knowledge_sources()
    document_indexes = build_document_indexes(sources)
    source_types = load_source_types(sources)

    evidence_matches: list[tuple[dict[str, Any], list[MatchResult]]] = []
    unmatched: list[dict[str, Any]] = []
    all_excluded: list[ExcludedMatch] = []

    for evidence in catalog:
        matches, excluded = find_references_for_evidence(
            evidence, document_indexes, source_types
        )
        all_excluded.extend(excluded)
        if matches:
            evidence_matches.append((evidence, matches))
        else:
            unmatched.append(evidence)

    evidence_matches.sort(key=lambda pair: evidence_sort_key(pair[0]))
    unmatched.sort(key=evidence_sort_key)

    report = build_report(
        scanned_pdf_count=len(document_indexes),
        evidence_count=len(catalog),
        evidence_matches=evidence_matches,
        unmatched=unmatched,
        source_types=source_types,
        excluded_matches=all_excluded,
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(REPORT_PATH)


if __name__ == "__main__":
    run()
