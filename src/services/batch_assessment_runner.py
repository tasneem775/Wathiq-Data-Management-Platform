"""Batch Assessment Runner.

Orchestrates running the assessment pipeline (assessment_pipeline_service.
run_assessment_pipeline) across every evidence code that has a matching
.docx file on disk for a domain. Discovers targets by combining
CatalogService.get_catalog() (for each MQ's evidence_folder) with
EvidenceService.scan() (for each MQ's matched_codes), builds the file_path
for each matched code, then runs the pipeline once per evidence code.

Each evidence code is isolated in its own try/except so that one failing
(or crashing) evidence file does not stop the rest of the batch.

No LLM, no OCR, no OpenAI/OpenRouter, no LangChain, no external API is
used here. Does not modify assessment_pipeline_service, EvidenceService,
or CatalogService.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from src.catalog.catalog_loader import CatalogLoadError
from src.catalog.catalog_service import CatalogService
from src.evidence.evidence_loader import EvidenceLoadError
from src.evidence.evidence_service import EvidenceService
from src.services.assessment_pipeline_service import run_assessment_pipeline


def build_evidence_targets(
    project_root: Path, domain_code: str = "DC"
) -> list[dict[str, str]]:
    """Combine the catalog and evidence scan to list every ready-to-assess evidence.

    Args:
        project_root: Absolute path to the project root directory.
        domain_code: Domain code this batch belongs to (currently informational
            only, since CatalogService/EvidenceService read a single fixed
            domain catalog).

    Returns:
        A list of target dicts, one per matched evidence code, each with
        "mq_id", "evidence_code", and "file_path".

    Raises:
        CatalogLoadError: If the domain catalog cannot be loaded or validated.
        EvidenceLoadError: If any MQ evidence JSON file cannot be loaded.
    """
    catalog = CatalogService(project_root).get_catalog()
    evidence_scan = EvidenceService(project_root).scan()

    folder_by_mq = {
        entry["mq_id"]: entry["evidence_folder"] for entry in catalog["mq_catalogs"]
    }

    targets: list[dict[str, str]] = []
    for mq_result in evidence_scan.mq_results:
        evidence_folder = folder_by_mq.get(mq_result.mq_id)
        if not evidence_folder:
            continue

        for code in mq_result.matched_codes:
            file_path = str(project_root / evidence_folder / f"{code}.docx")
            targets.append(
                {
                    "mq_id": mq_result.mq_id,
                    "evidence_code": code,
                    "file_path": file_path,
                }
            )

    return targets


def _summarize_batch(
    domain_code: str,
    targets: list[dict[str, str]],
    results: list[dict[str, Any]],
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    """Build the aggregate Batch Report from individual pipeline outcomes.

    Args:
        domain_code: Domain code this batch belongs to.
        targets: All evidence targets that were attempted.
        results: Pipeline result dicts for targets that ran without raising.
        errors: Isolated failure records for targets that raised an exception.

    Returns:
        A Batch Report dict summarizing counts and holding the raw results/errors.
    """
    success_count = sum(1 for r in results if r["pipeline_status"] == "success")
    human_review_count = sum(
        1 for r in results if r["pipeline_status"] == "human_review_required"
    )
    failed_count = sum(
        1
        for r in results
        if r["pipeline_status"] in ("file_read_failed", "assessment_failed")
    )

    return {
        "domain_code": domain_code,
        "total_targets": len(targets),
        "results": results,
        "errors": errors,
        "success_count": success_count,
        "human_review_count": human_review_count,
        "failed_count": failed_count,
        "error_count": len(errors),
    }


def run_batch_assessment(project_root: Path, domain_code: str = "DC") -> dict[str, Any]:
    """Run the assessment pipeline for every matched evidence code in the domain.

    Each evidence code is run in isolation: if run_assessment_pipeline raises
    an unexpected exception for one evidence code, it is recorded in the
    report's "errors" list and the batch continues with the next evidence code.

    Args:
        project_root: Absolute path to the project root directory.
        domain_code: Domain code this batch belongs to.

    Returns:
        A Batch Report dict (see _summarize_batch).

    Raises:
        CatalogLoadError: If the domain catalog cannot be loaded or validated.
        EvidenceLoadError: If any MQ evidence JSON file cannot be loaded.
    """
    targets = build_evidence_targets(project_root, domain_code)

    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for target in targets:
        try:
            result = run_assessment_pipeline(
                target["evidence_code"], target["file_path"]
            )
            results.append(result)
        except Exception as error:  # noqa: BLE001 - isolate one evidence failure from the batch
            errors.append(
                {
                    "evidence_code": target["evidence_code"],
                    "file_path": target["file_path"],
                    "error_message": str(error),
                }
            )

    return _summarize_batch(domain_code, targets, results, errors)


def _safe_print(line: str) -> None:
    try:
        print(line)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(line.encode(encoding, errors="replace").decode(encoding))


def main() -> None:
    """Command-line entry point.

    Usage:
        python -m src.services.batch_assessment_runner [domain_code]
    """
    domain_code = sys.argv[1] if len(sys.argv) > 1 else "DC"
    project_root = Path(__file__).resolve().parents[2]

    try:
        report = run_batch_assessment(project_root, domain_code)
    except (CatalogLoadError, EvidenceLoadError) as error:
        _safe_print(f"Batch assessment failed: {error}")
        return

    lines = [
        f"domain_code: {report['domain_code']}",
        f"total_targets: {report['total_targets']}",
        f"success_count: {report['success_count']}",
        f"human_review_count: {report['human_review_count']}",
        f"failed_count: {report['failed_count']}",
        f"error_count: {report['error_count']}",
    ]
    for line in lines:
        _safe_print(line)

    if report["errors"]:
        _safe_print("Errors:")
        for err in report["errors"]:
            _safe_print(f"  [{err['evidence_code']}] {err['error_message']}")


if __name__ == "__main__":
    main()
