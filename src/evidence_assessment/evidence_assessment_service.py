"""Evidence assessment service for maturity assessment orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.catalog.catalog_service import CatalogService
from src.evidence.evidence_service import EvidenceService
from src.evidence_assessment.evidence_assessment_evaluator import (
    EvidenceAssessmentEvaluator,
    MQLevelResult,
)
from src.evidence_assessment.evidence_assessment_loader import EvidenceAssessmentLoader


@dataclass
class EvidenceAssessmentReport:
    """Full evidence assessment report for a domain.

    Attributes:
        domain_name_ar: Arabic display name of the assessed domain.
        domain_code: Short domain code (e.g. "DC").
        mq_results: Ordered list of per-MQ evaluation results.
    """

    domain_name_ar: str
    domain_code: str
    mq_results: list[MQLevelResult] = field(default_factory=list)

    @property
    def overall_level(self) -> int:
        """Conservative domain score: minimum achieved level across all MQs."""
        if not self.mq_results:
            return 0
        return min(result.achieved_level for result in self.mq_results)


class EvidenceAssessmentService:
    """Orchestrates evidence assessment using catalog, evidence, and maturity models.

    Reads the domain catalog to discover MQ metadata, runs an evidence scan
    to determine which evidence files exist, loads the maturity model for each
    MQ, and delegates level evaluation to EvidenceAssessmentEvaluator.

    Attributes:
        _project_root: Absolute path to the project root.
        _catalog_service: Provides the domain catalog and MQ metadata.
        _evidence_service: Scans evidence files against the catalog.
        _loader: Reads individual maturity model JSON files.
        _evaluator: Computes the achieved maturity level for each MQ.
    """

    def __init__(self, project_root: Path) -> None:
        """Args:
            project_root: Absolute path to the project root directory.
        """
        self._project_root = project_root
        self._catalog_service = CatalogService(project_root)
        self._evidence_service = EvidenceService(project_root)
        self._loader = EvidenceAssessmentLoader()
        self._evaluator = EvidenceAssessmentEvaluator()

    def assess(self) -> EvidenceAssessmentReport:
        """Run a full evidence assessment across all MQs in the domain catalog.

        For each MQ entry in the catalog, loads the corresponding maturity model
        and evidence scan result, then evaluates the achieved maturity level.

        Returns:
            An EvidenceAssessmentReport with per-MQ maturity levels and overall domain level.

        Raises:
            CatalogLoadError: If the domain catalog cannot be loaded or validated.
            EvidenceLoadError: If any MQ evidence JSON file cannot be loaded.
            EvidenceAssessmentLoadError: If any maturity model JSON file cannot be loaded.
        """
        catalog = self._catalog_service.get_catalog()
        domain = catalog["domain"]

        evidence_scan = self._evidence_service.scan()
        scan_by_mq = {result.mq_id: result for result in evidence_scan.mq_results}

        report = EvidenceAssessmentReport(
            domain_name_ar=domain["name_ar"],
            domain_code=domain["code"],
        )

        for mq_entry in catalog["mq_catalogs"]:
            mq_id: str = mq_entry["mq_id"]
            requirements_file = self._project_root / mq_entry["requirements_file"]

            model_data = self._loader.load(requirements_file)
            validation = scan_by_mq.get(mq_id)

            if validation is None:
                continue

            result = self._evaluator.evaluate(mq_id, model_data, validation)
            report.mq_results.append(result)

        return report
