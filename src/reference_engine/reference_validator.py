"""Reference Validator.

An independent checker for the Reference Engine's output. It reads:

1. The Knowledge Catalog (the list of Evidence records that must be covered).
2. The registered knowledge sources (knowledge_base/knowledge_sources.json).
3. The engine's own report (reports/reference_engine_report.txt).
4. The registered PDF files themselves, opened directly with PyMuPDF.

...and cross-checks the report's claims against the actual PDFs rather than
trusting the report at face value: every reported page number is opened and
its real text is inspected to confirm the evidence code or name is really
there, page_role classifications are checked against the phrases/source
types that justify them, and excluded matches are confirmed absent from the
accepted matches.

No AI, embeddings, semantic search, or OCR is used - only plain substring
checks over text extracted with PyMuPDF, the same as the engine itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.reference_engine.reference_engine import (
    PROJECT_ROOT,
    REPORT_PATH,
    PageEntry,
    build_document_indexes,
    load_knowledge_catalog,
    load_knowledge_sources,
    load_source_types,
)

VALIDATION_REPORT_PATH = PROJECT_ROOT / "reports" / "reference_validation_report.txt"

# The requirement phrasing the validator itself insists on for any match
# classified as a Detailed Requirement Page. Checked against normalized text
# (see normalize_arabic_text) so that PDF line-wrapping - which can split a
# phrase like "يجب على الجهة" across three separate lines - does not cause a
# false negative.
REQUIRED_DETAIL_PHRASES = (
    "يجب على الجهة",
    "يجب إرفاق",
    "كحد أدنى",
    "يجب أن تشمل",
    "على الجهة",
    "ينبغي أن يشمل",
    "معايير قبول",
    "الأدلة الداعمة",
    "الوثائق والأدلة الداعمة",
)

# Arabic combining marks (tashkeel) and the tatweel elongation character -
# stripped before phrase matching since their presence or absence in the
# source PDF text is not meaningful for a plain substring check.
ARABIC_DIACRITICS_PATTERN = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۨ-ۭـ]")

# Alef and hamza variants folded onto a single bare alef so that a phrase
# spelled with a plain "ا" still matches text that used "أ"/"إ"/"آ" (or vice
# versa) for the same word.
ALEF_VARIANTS_PATTERN = re.compile(r"[إأآا]")

WHITESPACE_PATTERN = re.compile(r"\s+")

SEPARATOR = "-" * 50


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text for a resilient phrase search.

    PDF text extraction can split what is visually one phrase across several
    lines (each word on its own line), and can freely mix diacritics or Alef/
    Hamza spelling variants that are irrelevant to a plain substring check.
    This collapses all whitespace (including newlines) to single spaces,
    strips diacritics and tatweel, and folds Alef/Hamza variants together -
    so both the page text and the search phrases can be compared on equal
    footing regardless of how the PDF happened to wrap or spell them.
    """
    text = ARABIC_DIACRITICS_PATTERN.sub("", text)
    text = ALEF_VARIANTS_PATTERN.sub("ا", text)
    text = WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()


NORMALIZED_REQUIRED_DETAIL_PHRASES = tuple(
    normalize_arabic_text(phrase) for phrase in REQUIRED_DETAIL_PHRASES
)


@dataclass
class ReportedMatch:
    """One reference entry as parsed back out of the engine's report."""

    document_name: str
    source_type_in_report: str
    page_number: int
    matched_by: str
    confidence: str
    page_role: str
    matched_text: str
    context: str


@dataclass
class ReportedEvidence:
    """One Evidence block as parsed back out of the engine's report."""

    evidence_code: str
    evidence_name: str
    mq_id: str
    level_name: str
    matches: list[ReportedMatch]


@dataclass
class ReportedExclusion:
    """One excluded-match entry as parsed back out of the engine's report."""

    evidence_code: str
    evidence_name: str
    document_name: str
    page_number: int
    matched_by: str
    matched_text: str
    reason: str
    context: str


@dataclass
class CheckResult:
    """One pass/fail assertion made by the validator."""

    evidence_code: str
    check_name: str
    passed: bool
    detail: str


def extract_between(text: str, start_label: str, end_label: str | None) -> str:
    """Return the value following "start_label:\\n" up to "end_label:\\n" (or EOF)."""
    start_marker = start_label + ":\n"
    start_index = text.find(start_marker)
    if start_index == -1:
        return ""
    start_index += len(start_marker)
    if end_label is None:
        return text[start_index:].strip()
    end_index = text.find(end_label + ":\n", start_index)
    if end_index == -1:
        return text[start_index:].strip()
    return text[start_index:end_index].strip()


def parse_header_stats(report_text: str) -> dict[str, int]:
    """Pull the summary counters printed at the top of the engine's report."""
    patterns = {
        "scanned_pdf_count": r"عدد ملفات PDF التي تم فحصها: (\d+)",
        "evidence_count": r"عدد الأدلة: (\d+)",
        "total_matches": r"عدد المطابقات: (\d+)",
        "unmatched_count": r"عدد الأدلة التي لم يتم العثور عليها: (\d+)",
        "excluded_count": r"عدد المطابقات المستبعدة: (\d+)",
    }
    stats: dict[str, int] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, report_text)
        stats[key] = int(match.group(1)) if match else -1
    return stats


def parse_match_block(block: str) -> ReportedMatch:
    """Parse one "مرجع رقم (i)" block into a ReportedMatch."""
    document_name = extract_between(block, "اسم الملف", "نوع المرجع")
    source_type_in_report = extract_between(block, "نوع المرجع", "رقم الصفحة")
    page_number_text = extract_between(block, "رقم الصفحة", "طريقة المطابقة")
    matched_by = extract_between(block, "طريقة المطابقة", "درجة الثقة")
    confidence = extract_between(block, "درجة الثقة", "page_role")
    page_role = extract_between(block, "page_role", "النص المطابق")
    matched_text = extract_between(block, "النص المطابق", "سياق المطابقة")
    context = extract_between(block, "سياق المطابقة", None)
    try:
        page_number = int(page_number_text)
    except ValueError:
        page_number = -1
    return ReportedMatch(
        document_name=document_name,
        source_type_in_report=source_type_in_report,
        page_number=page_number,
        matched_by=matched_by,
        confidence=confidence,
        page_role=page_role,
        matched_text=matched_text,
        context=context,
    )


def parse_evidence_blocks(body_text: str) -> list[ReportedEvidence]:
    """Split the report's body into per-Evidence blocks and parse each one."""
    sections = re.split(r"-{50}\nرمز الدليل:\n", body_text)
    evidences: list[ReportedEvidence] = []
    for section in sections[1:]:
        evidence_code, _, remainder = section.partition("\n\n")
        evidence_code = evidence_code.strip()

        first_separator = remainder.find(SEPARATOR)
        header_region = remainder[:first_separator] if first_separator != -1 else remainder
        matches_region = remainder[first_separator:] if first_separator != -1 else ""

        evidence_name = extract_between(header_region, "اسم الدليل", "السؤال")
        mq_id = extract_between(header_region, "السؤال", "المستوى")
        level_name = extract_between(header_region, "المستوى", "عدد المراجع المكتشفة")

        match_blocks = [
            block.strip() for block in matches_region.split(SEPARATOR) if block.strip()
        ]
        matches = [parse_match_block(block) for block in match_blocks if "اسم الملف:" in block]

        evidences.append(
            ReportedEvidence(
                evidence_code=evidence_code,
                evidence_name=evidence_name,
                mq_id=mq_id,
                level_name=level_name,
                matches=matches,
            )
        )
    return evidences


def parse_unmatched_codes(report_text: str) -> set[str]:
    """Return the Evidence codes listed under "أدلة بدون أي مرجع"."""
    start = report_text.find("أدلة بدون أي مرجع")
    end = report_text.find("مطابقات مستبعدة")
    if start == -1:
        return set()
    section = report_text[start:end if end != -1 else len(report_text)]
    codes = set()
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("- ")]
    # Lines alternate: "- <code>", "- <name>" - only the code lines matter here,
    # and codes never contain spaces while Evidence names always do.
    for line in lines:
        value = line[2:].strip()
        if value and " " not in value:
            codes.add(value)
    return codes


def parse_excluded_matches(report_text: str) -> list[ReportedExclusion]:
    """Parse the "مطابقات مستبعدة" section into ReportedExclusion entries."""
    start = report_text.find("مطابقات مستبعدة")
    if start == -1:
        return []
    section = report_text[start:]
    blocks = [block.strip() for block in section.split(SEPARATOR) if block.strip()]
    exclusions: list[ReportedExclusion] = []
    for block in blocks:
        if "evidence_code:" not in block:
            continue
        evidence_code = extract_between(block, "evidence_code", "evidence_name")
        evidence_name = extract_between(block, "evidence_name", "document_name")
        document_name = extract_between(block, "document_name", "page_number")
        page_number_text = extract_between(block, "page_number", "matched_by")
        matched_by = extract_between(block, "matched_by", "matched_text")
        matched_text = extract_between(block, "matched_text", "سبب الاستبعاد")
        reason = extract_between(block, "سبب الاستبعاد", "جزء من السياق")
        context = extract_between(block, "جزء من السياق", None)
        try:
            page_number = int(page_number_text)
        except ValueError:
            page_number = -1
        exclusions.append(
            ReportedExclusion(
                evidence_code=evidence_code,
                evidence_name=evidence_name,
                document_name=document_name,
                page_number=page_number,
                matched_by=matched_by,
                matched_text=matched_text,
                reason=reason,
                context=context,
            )
        )
    return exclusions


def check_pdf_count(
    checks: list[CheckResult], registered_count: int, header_stats: dict[str, int]
) -> None:
    """Test 1: registered PDF count must match the report's scanned count."""
    scanned = header_stats.get("scanned_pdf_count", -1)
    passed = registered_count == scanned
    checks.append(
        CheckResult(
            evidence_code="-",
            check_name="عدد ملفات PDF المسجلة يطابق عدد الملفات المفحوصة",
            passed=passed,
            detail=f"مسجلة في knowledge_sources.json: {registered_count} | مفحوصة في التقرير: {scanned}",
        )
    )


def get_page_text(
    document_indexes: dict[str, list[PageEntry]], document_name: str, page_number: int
) -> str | None:
    """Return the extracted text of one page, or None if it cannot be found."""
    pages = document_indexes.get(document_name)
    if pages is None:
        return None
    for page in pages:
        if page.page_number == page_number:
            return page.extracted_text
    return None


def check_evidence_matches(
    checks: list[CheckResult],
    evidence: dict[str, Any],
    reported: ReportedEvidence | None,
    unmatched_codes: set[str],
    document_indexes: dict[str, list[PageEntry]],
    source_types: dict[str, str],
) -> None:
    """Run every per-Evidence / per-match assertion for one Evidence record."""
    evidence_code = evidence["evidence_code"]
    evidence_name = evidence["evidence_name"]

    match_count = len(reported.matches) if reported else 0
    has_reference = match_count >= 1 and evidence_code not in unmatched_codes
    checks.append(
        CheckResult(
            evidence_code=evidence_code,
            check_name="له مرجع واحد على الأقل",
            passed=has_reference,
            detail=f"عدد المراجع في التقرير: {match_count}",
        )
    )
    if reported is None:
        return

    for index, match in enumerate(reported.matches, start=1):
        label = f"مرجع رقم ({index}) - {match.document_name} - صفحة {match.page_number}"

        pages = document_indexes.get(match.document_name)
        page_exists = pages is not None and 1 <= match.page_number <= len(pages)
        checks.append(
            CheckResult(
                evidence_code=evidence_code,
                check_name=f"{label}: رقم الصفحة موجود داخل PDF",
                passed=page_exists,
                detail=(
                    f"عدد صفحات الملف: {len(pages) if pages is not None else 'غير معروف'}"
                ),
            )
        )
        if not page_exists:
            continue

        page_text = get_page_text(document_indexes, match.document_name, match.page_number)
        contains_evidence = bool(
            page_text is not None
            and (evidence_code in page_text or evidence_name in page_text)
        )
        checks.append(
            CheckResult(
                evidence_code=evidence_code,
                check_name=f"{label}: الصفحة تحتوي evidence_code أو evidence_name",
                passed=contains_evidence,
                detail="تم فتح الصفحة والتحقق من محتواها الفعلي داخل ملف PDF",
            )
        )

        if match.page_role == "Detailed Requirement Page":
            normalized_page_text = normalize_arabic_text(page_text) if page_text is not None else ""
            has_phrase = any(
                phrase in normalized_page_text for phrase in NORMALIZED_REQUIRED_DETAIL_PHRASES
            )
            checks.append(
                CheckResult(
                    evidence_code=evidence_code,
                    check_name=f"{label}: Detailed Requirement Page تحتوي عبارة متطلبات",
                    passed=has_phrase,
                    detail="يبحث عن (بعد التطبيع): " + " / ".join(REQUIRED_DETAIL_PHRASES),
                )
            )

        if match.page_role == "Official Maturity Reference":
            actual_type = source_types.get(match.document_name, "")
            passed = actual_type == "Official Reference"
            checks.append(
                CheckResult(
                    evidence_code=evidence_code,
                    check_name=f"{label}: Official Maturity Reference يطابق source_type",
                    passed=passed,
                    detail=f"source_type الفعلي المسجل: {actual_type}",
                )
            )

        if match.page_role == "Supporting Policy Page":
            actual_type = source_types.get(match.document_name, "")
            passed = actual_type == "Supporting Official Reference"
            checks.append(
                CheckResult(
                    evidence_code=evidence_code,
                    check_name=f"{label}: Supporting Policy Page يطابق source_type",
                    passed=passed,
                    detail=f"source_type الفعلي المسجل: {actual_type}",
                )
            )


def check_exclusions_not_accepted(
    checks: list[CheckResult],
    evidences: list[ReportedEvidence],
    exclusions: list[ReportedExclusion],
) -> None:
    """Test 3: an excluded match must not also appear among accepted matches."""
    accepted_keys: set[tuple[str, str, int, str, str]] = set()
    for evidence in evidences:
        for match in evidence.matches:
            accepted_keys.add(
                (
                    evidence.evidence_code,
                    match.document_name,
                    match.page_number,
                    match.matched_by,
                    match.matched_text,
                )
            )

    for exclusion in exclusions:
        key = (
            exclusion.evidence_code,
            exclusion.document_name,
            exclusion.page_number,
            exclusion.matched_by,
            exclusion.matched_text,
        )
        passed = key not in accepted_keys
        checks.append(
            CheckResult(
                evidence_code=exclusion.evidence_code,
                check_name=(
                    f"مطابقة مستبعدة ({exclusion.document_name} / صفحة {exclusion.page_number}) "
                    "غير موجودة ضمن المراجع المقبولة"
                ),
                passed=passed,
                detail=exclusion.reason,
            )
        )


def build_validation_report(checks: list[CheckResult], evidence_count: int) -> str:
    """Render the Arabic validation report."""
    evaluated_evidence_codes = {check.evidence_code for check in checks if check.evidence_code != "-"}
    passed_checks = sum(1 for check in checks if check.passed)
    failed_checks = sum(1 for check in checks if not check.passed)
    overall = "PASS" if failed_checks == 0 else "FAIL"

    lines: list[str] = []
    lines.append("=" * 50)
    lines.append("تقرير التحقق من محرك اكتشاف المراجع")
    lines.append("Reference Validator Report")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"عدد الأدلة: {evidence_count}")
    lines.append("")
    lines.append(f"عدد الأدلة التي تم التحقق منها: {len(evaluated_evidence_codes)}")
    lines.append("")
    lines.append(f"عدد الاختبارات الناجحة: {passed_checks}")
    lines.append("")
    lines.append(f"عدد الاختبارات الفاشلة: {failed_checks}")
    lines.append("")
    lines.append(f"النتيجة النهائية: {overall}")
    lines.append("")
    lines.append("=" * 50)
    lines.append("")

    current_code: str | None = None
    for check in checks:
        if check.evidence_code != current_code:
            current_code = check.evidence_code
            lines.append(SEPARATOR)
            lines.append("رمز الدليل:" if current_code != "-" else "فحص عام:")
            lines.append(current_code)
            lines.append(SEPARATOR)
            lines.append("")

        status = "PASS" if check.passed else "FAIL"
        lines.append(f"[{status}] {check.check_name}")
        lines.append(check.detail)
        lines.append("")

    return "\n".join(lines) + "\n"


def run() -> None:
    """Entry point: parse the engine's report, validate it, and save the results."""
    catalog = load_knowledge_catalog()
    sources = load_knowledge_sources()
    source_types = load_source_types(sources)
    document_indexes = build_document_indexes(sources)

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    header_stats = parse_header_stats(report_text)

    excluded_start = report_text.find("مطابقات مستبعدة")
    body_end = report_text.find("أدلة بدون أي مرجع")
    body_text = report_text[: body_end if body_end != -1 else excluded_start]

    evidences = parse_evidence_blocks(body_text)
    evidences_by_code = {evidence.evidence_code: evidence for evidence in evidences}
    unmatched_codes = parse_unmatched_codes(report_text)
    exclusions = parse_excluded_matches(report_text)

    checks: list[CheckResult] = []

    check_pdf_count(checks, len(sources), header_stats)

    for evidence in catalog:
        reported = evidences_by_code.get(evidence["evidence_code"])
        check_evidence_matches(
            checks, evidence, reported, unmatched_codes, document_indexes, source_types
        )

    check_exclusions_not_accepted(checks, evidences, exclusions)

    report = build_validation_report(checks, len(catalog))

    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_REPORT_PATH.write_text(report, encoding="utf-8")

    evaluated_evidence_codes = {check.evidence_code for check in checks if check.evidence_code != "-"}
    passed_checks = sum(1 for check in checks if check.passed)
    failed_checks = sum(1 for check in checks if not check.passed)
    overall = "PASS" if failed_checks == 0 else "FAIL"

    print(f"عدد الأدلة: {len(catalog)}")
    print(f"عدد الأدلة التي تم التحقق منها: {len(evaluated_evidence_codes)}")
    print(f"عدد الاختبارات الناجحة: {passed_checks}")
    print(f"عدد الاختبارات الفاشلة: {failed_checks}")
    print(f"النتيجة النهائية: {overall}")
    print(VALIDATION_REPORT_PATH)


if __name__ == "__main__":
    run()
