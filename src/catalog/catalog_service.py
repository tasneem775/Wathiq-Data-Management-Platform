"""Catalog service for the NDI-Sentinel project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.catalog.catalog_loader import CatalogLoader, CatalogLoadError
from src.catalog.catalog_validator import CatalogValidator


class CatalogService:
    """Unified interface for loading and validating the domain evidence catalog.

    All system components (Compliance Engine, Dashboard, AI Agents, Backend)
    interact with the catalog exclusively through this service.

    Attributes:
        _loader: Responsible for reading and parsing the catalog file.
        _validator: Responsible for structural and path validation.
        _project_root: Absolute path to the project root directory.
    """

    def __init__(self, project_root: Path) -> None:
        """Args:
            project_root: Absolute path to the project root directory.
        """
        self._loader = CatalogLoader(project_root)
        self._validator = CatalogValidator()
        self._project_root = project_root

    def get_catalog(self) -> dict[str, Any]:
        """Load and structurally validate the catalog.

        Returns:
            A fully validated catalog dictionary ready for consumption.

        Raises:
            CatalogLoadError: If the file cannot be read or fails structural validation.
        """
        catalog = self._loader.load()
        self._validator.validate_structure(catalog)
        return catalog

    def validate_referenced_paths(self) -> list[str]:
        """Load the catalog and return a list of path validation errors.

        Returns:
            A list of path error messages. An empty list means all paths are valid.

        Raises:
            CatalogLoadError: If the catalog cannot be loaded or fails structural validation.
        """
        catalog = self.get_catalog()
        return self._validator.validate_paths(catalog, self._project_root)
