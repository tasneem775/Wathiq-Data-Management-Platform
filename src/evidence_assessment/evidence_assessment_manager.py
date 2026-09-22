"""Entry point for the evidence assessment engine."""

from __future__ import annotations

from pathlib import Path

from src.catalog.catalog_service import CatalogService
from src.evidence.evidence_service import EvidenceService
from src.evidence_assessment.evidence_assessment_evaluator import MQLevelResult
from src.evidence_assessment.evidence_assessment_service import (
    EvidenceAssessmentReport,
    EvidenceAssessmentService,
)

_WIDE = 66
_NARROW = 50
_LABEL_COL = 26
_SUMMARY_COL = 28

_SEP_WIDE = "=" * _WIDE
_SEP_NARROW = "-" * _NARROW
_SEP_SECTION = "-" * 32


def _row(label: str, value: object, col: int = _LABEL_COL) -> str:
    return f"  {label:<{col}}: {value}"


def _print_header() -> None:
    title = "NDI Evidence Assessment Report"
    print(_SEP_WIDE)
    print(title.center(_WIDE))
    print(_SEP_WIDE)


def _print_domain_info(name_ar: str, code: str) -> None:
    print()
    print(f"  Domain   : {name_ar}")
    print(f"  Code     : {code}")
    print()


def _build_table(headers: list[str], rows: list[list[str]]) -> str:
    """Build a plain-text bordered table with auto-sized columns.

    Args:
        headers: Column header labels.
        rows: Data rows, each a list of string values aligned to headers.

    Returns:
        Formatted table as a multi-line string ready to print.
    """
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def _rule() -> str:
        return "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    def _data_row(cells: list[str]) -> str:
        parts = [f" {cell:<{col_widths[i]}} " for i, cell in enumerate(cells)]
        return "|" + "|".join(parts) + "|"

    lines = [_rule(), _data_row(headers), _rule()]
    for row in rows:
        lines.append(_data_row(row))
    lines.append(_rule())
    return "\n".join(lines)


def _print_summary_table(
    assessment_report: EvidenceAssessmentReport,
    required_by_mq: dict[str, list[str]],
) -> None:
    """Print a compact summary table of all MQ results.

    Args:
        assessment_report: The full evidence assessment report.
        required_by_mq: Mapping from mq_id to required evidence codes.
    """
    headers = ["MQ", "Required", "Available", "Coverage", "Availability", "Status"]
    rows: list[list[str]] = []

    for mq_result in assessment_report.mq_results:
        req = len(required_by_mq.get(mq_result.mq_id, []))
        avail = len(mq_result.present_codes)
        cov = (avail / req * 100.0) if req > 0 else 0.0
        availability = "COMPLETE" if cov >= 100.0 else "INCOMPLETE"
        status = "PASSED" if cov >= 100.0 else "INCOMPLETE"
        rows.append([
            mq_result.mq_id,
            str(req),
            str(avail),
            f"{cov:.1f}%",
            availability,
            status,
        ])

    print(_build_table(headers, rows))
    print()


def _print_mq_block(
    result: MQLevelResult,
    required_count: int,
    evidence_folder: str,
) -> None:
    """Print a single MQ assessment block with evidence list and file paths.

    Args:
        result: Maturity level evaluation result for this MQ.
        required_count: Total number of required evidence items from the catalog.
        evidence_folder: Relative path to the MQ evidence folder.
    """
    available = len(result.present_codes)
    coverage = (available / required_count * 100.0) if required_count > 0 else 0.0
    availability = "COMPLETE" if coverage >= 100.0 else "INCOMPLETE"
    status = "PASSED" if coverage >= 100.0 else "INCOMPLETE"

    print(_SEP_NARROW)
    print(f"  MQ : {result.mq_id}")
    print(_SEP_NARROW)
    print()
    print(_row("Required Evidence", required_count))
    print(_row("Available Evidence", available))
    print(_row("Coverage", f"{coverage:.1f}%"))
    print(_row("Evidence Availability", availability))
    print(_row("Assessment Status", status))
    print()

    print("  Evidence List")
    print("  " + _SEP_SECTION)
    for code in result.present_codes:
        print(f"    [+] {code}")
    print()

    print("  Evidence Files")
    print("  " + _SEP_SECTION)
    for code in result.present_codes:
        file_path = f"{evidence_folder}/{code}.docx"
        print(f"    {code}")
        print(f"      {file_path}")
        print()


def _print_summary(
    report: EvidenceAssessmentReport,
    total_required: int,
    total_available: int,
) -> None:
    """Print the overall domain summary block.

    Args:
        report: The assembled evidence assessment report.
        total_required: Sum of required evidence items across all MQs.
        total_available: Sum of available evidence items across all MQs.
    """
    coverage = (total_available / total_required * 100.0) if total_required > 0 else 0.0
    availability = "COMPLETE" if coverage >= 100.0 else "INCOMPLETE"
    status = "PASSED" if coverage >= 100.0 else "INCOMPLETE"

    print(_SEP_WIDE)
    print()
    print("  Overall Summary")
    print()
    print(_row("Total MQs", len(report.mq_results), _SUMMARY_COL))
    print(_row("Total Required Evidence", total_required, _SUMMARY_COL))
    print(_row("Total Available Evidence", total_available, _SUMMARY_COL))
    print(_row("Overall Coverage", f"{coverage:.1f}%", _SUMMARY_COL))
    print(_row("Overall Evidence Availability", availability, _SUMMARY_COL))
    print(_row("Assessment Status", status, _SUMMARY_COL))
    print()
    print(_SEP_WIDE)


def main() -> None:
    """Run the evidence assessment and print the formatted report to the terminal."""
    project_root = Path(__file__).resolve().parents[2]

    assessment_report = EvidenceAssessmentService(project_root).assess()
    evidence_scan = EvidenceService(project_root).scan()
    catalog = CatalogService(project_root).get_catalog()

    required_by_mq = {
        r.mq_id: r.required_codes
        for r in evidence_scan.mq_results
    }
    folder_by_mq = {
        entry["mq_id"]: entry["evidence_folder"]
        for entry in catalog["mq_catalogs"]
    }

    _print_header()
    _print_domain_info(assessment_report.domain_name_ar, assessment_report.domain_code)
    _print_summary_table(assessment_report, required_by_mq)

    total_required = 0
    total_available = 0

    for mq_result in assessment_report.mq_results:
        required_codes = required_by_mq.get(mq_result.mq_id, [])
        evidence_folder = folder_by_mq.get(mq_result.mq_id, "")

        _print_mq_block(mq_result, len(required_codes), evidence_folder)

        total_required += len(required_codes)
        total_available += len(mq_result.present_codes)

    _print_summary(assessment_report, total_required, total_available)


if __name__ == "__main__":
    main()
