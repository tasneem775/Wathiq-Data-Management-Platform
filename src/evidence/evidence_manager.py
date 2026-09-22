"""Entry point for running the evidence scan report."""

from __future__ import annotations

from pathlib import Path

from src.catalog.catalog_loader import CatalogLoadError
from src.evidence.evidence_loader import EvidenceLoadError
from src.evidence.evidence_service import EvidenceScanReport, EvidenceService


def _print_report(report: EvidenceScanReport) -> None:
    """Format and print the evidence scan report to stdout.

    Args:
        report: The completed scan report to display.
    """
    print("Evidence Scan Report")
    print(f"Domain: {report.domain_name_ar} ({report.domain_code})")

    for result in report.mq_results:
        print(f"\nMQ: {result.mq_id}")
        print(f"Required Evidence : {len(result.required_codes)}")
        print(f"Matched Evidence  : {len(result.matched_codes)}")
        print(f"Missing Evidence  : {len(result.missing_codes)}")
        print(f"Extra Files       : {len(result.extra_files)}")

        for code in result.missing_codes:
            print(f"  [MISSING] {code}.docx")

        for name in result.extra_files:
            print(f"  [EXTRA]   {name}.docx")

    print("\nOverall")
    print(f"Total Required    : {report.total_required}")
    print(f"Total Matched     : {report.total_matched}")
    print(f"Total Missing     : {report.total_missing}")
    print(f"Total Extra Files : {report.total_extra}")


def main() -> None:
    """Run the evidence scan and print the report."""
    project_root = Path(__file__).resolve().parents[2]
    service = EvidenceService(project_root)

    try:
        report = service.scan()
    except (CatalogLoadError, EvidenceLoadError) as error:
        print(f"Evidence scan failed: {error}")
        return

    _print_report(report)


if __name__ == "__main__":
    main()
