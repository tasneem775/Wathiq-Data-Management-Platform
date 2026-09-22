"""Catalog loader for the NDI-Sentinel project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CatalogLoadError(Exception):
    """Raised when the evidence catalog file cannot be loaded."""


class CatalogLoader:
    """Reads and parses the domain evidence catalog JSON file.

    Responsible solely for I/O: locating the file, reading it, and converting
    it to a Python dictionary. No validation logic is performed here.

    Attributes:
        _catalog_path: Absolute path to the catalog JSON file.
    """

    _RELATIVE_PATH: Path = (
        Path("data") / "evidence_catalog" / "dc_evidence_catalog.json"
    )

    def __init__(self, project_root: Path) -> None:
        """Args:
            project_root: Absolute path to the project root directory.
        """
        self._catalog_path = project_root / self._RELATIVE_PATH

    def load(self) -> dict[str, Any]:
        """Read the catalog JSON file and return it as a dictionary.

        Returns:
            Parsed catalog data as a Python dictionary.

        Raises:
            CatalogLoadError: If the file does not exist or contains invalid JSON.
        """
        if not self._catalog_path.exists():
            raise CatalogLoadError(
                f"Catalog file not found: {self._catalog_path}"
            )

        try:
            with self._catalog_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise CatalogLoadError(
                f"Invalid JSON format: {self._catalog_path}"
            ) from error
