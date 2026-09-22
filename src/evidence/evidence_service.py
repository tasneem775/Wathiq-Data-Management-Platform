"""Evidence service for the NDI-Sentinel project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.catalog.catalog_loader import CatalogLoadError
from src.catalog.catalog_service import CatalogService
from src.evidence.evidence_loader import EvidenceLoader, EvidenceLoadError
from src.evidence.evidence_validator import EvidenceValidator, MQValidationResult


@dataclass
class EvidenceScanReport:
    """Aggregated scan result across all MQs in a domain.

    Attributes:
        domain_name_ar: Arabic display name of the domain.
        domain_code: Short domain code (e.g. "DC").
        mq_results: Ordered list of per-MQ validation results.
    """

    domain_name_ar: str
    domain_code: str
    mq_results: list[MQValidationResult] = field(default_factory=list)

    @property
    def total_required(self) -> int:
        """Total number of required evidence items across all MQs."""
        return sum(len(r.required_codes) for r in self.mq_results)

    @property
    def total_matched(self) -> int:
        """Total number of matched evidence items across all MQs."""
        return sum(len(r.matched_codes) for r in self.mq_results)

    @property
    def total_missing(self) -> int:
        """Total number of missing evidence items across all MQs."""
        return sum(len(r.missing_codes) for r in self.mq_results)

    @property
    def total_extra(self) -> int:
        """Total number of extra files across all MQs."""
        return sum(len(r.extra_files) for r in self.mq_results)


class EvidenceService:
    """Orchestrates catalog reading, evidence loading, and validation.

    Uses CatalogService to discover MQ entries, EvidenceLoader to parse each
    MQ evidence JSON, and EvidenceValidator to compare codes against disk files.
    """

    def __init__(self, project_root: Path) -> None:
        """Args:
            project_root: Absolute path to the project root directory.
        """
        self._project_root = project_root
        self._catalog_service = CatalogService(project_root)
        self._loader = EvidenceLoader()
        self._validator = EvidenceValidator()

    def scan(self) -> EvidenceScanReport:
        """Run a full evidence scan across all MQs in the domain catalog.

        Returns:
            An EvidenceScanReport containing per-MQ and overall results.

        Raises:
            CatalogLoadError: If the domain catalog cannot be loaded or validated.
            EvidenceLoadError: If any MQ evidence JSON file cannot be loaded.
        """
        catalog = self._catalog_service.get_catalog()
        domain = catalog["domain"]

        report = EvidenceScanReport(
            domain_name_ar=domain["name_ar"],
            domain_code=domain["code"],
        )

        for mq_entry in catalog["mq_catalogs"]:
            catalog_file = self._project_root / mq_entry["catalog_file"]
            evidence_folder = self._project_root / mq_entry["evidence_folder"]

            mq_data = self._loader.load(catalog_file)
            result = self._validator.validate(
                mq_id=mq_entry["mq_id"],
                evidence_items=mq_data["evidence_items"],
                evidence_folder=evidence_folder,
            )
            report.mq_results.append(result)

        return report
