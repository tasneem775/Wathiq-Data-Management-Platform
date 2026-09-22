"""Catalog validator for the NDI-Sentinel project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.catalog.catalog_loader import CatalogLoadError


class CatalogValidationError(CatalogLoadError):
    """Raised when catalog structure or referenced paths fail validation."""


class CatalogValidator:
    """Validates structure and referenced paths of a pre-loaded catalog dictionary.

    Receives a dictionary from CatalogLoader and performs all structural
    and filesystem checks. Does not perform any file I/O itself.
    """

    _REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "catalog_type",
        "domain",
        "version",
        "status",
        "mq_catalogs",
        "summary",
    )
    _MQ_PATH_FIELDS: tuple[str, ...] = (
        "catalog_file",
        "requirements_file",
        "evidence_folder",
    )

    def validate_structure(self, catalog: dict[str, Any]) -> None:
        """Validate required fields and field types in the catalog.

        Args:
            catalog: Pre-loaded catalog dictionary to validate.

        Raises:
            CatalogValidationError: If required fields are missing or malformed.
        """
        missing = [f for f in self._REQUIRED_FIELDS if f not in catalog]
        if missing:
            raise CatalogValidationError(
                f"Missing required catalog fields: {', '.join(missing)}"
            )

        if not isinstance(catalog["mq_catalogs"], list):
            raise CatalogValidationError("Field 'mq_catalogs' must be a list.")

    def validate_paths(
        self, catalog: dict[str, Any], project_root: Path
    ) -> list[str]:
        """Check that all referenced file and folder paths exist on disk.

        Args:
            catalog: Pre-loaded catalog dictionary.
            project_root: Absolute path to the project root directory.

        Returns:
            A list of error messages for each missing path or field.
            Returns an empty list when all paths are valid.
        """
        errors: list[str] = []

        for mq_catalog in catalog["mq_catalogs"]:
            for field in self._MQ_PATH_FIELDS:
                relative_path = mq_catalog.get(field)

                if not relative_path:
                    errors.append(
                        f"{mq_catalog.get('mq_id', 'UNKNOWN')}: missing field '{field}'"
                    )
                    continue

                if not (project_root / relative_path).exists():
                    errors.append(
                        f"{mq_catalog.get('mq_id', 'UNKNOWN')}: path not found: {relative_path}"
                    )

        return errors
