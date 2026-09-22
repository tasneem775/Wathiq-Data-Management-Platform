"""Evidence assessment loader for maturity model JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EvidenceAssessmentLoadError(Exception):
    """Raised when a maturity model file cannot be loaded or parsed."""


class EvidenceAssessmentLoader:
    """Reads and parses a single maturity model JSON file.

    Responsible solely for file I/O and JSON decoding.
    No validation or evaluation logic is performed here.
    """

    def load(self, file_path: Path) -> dict[str, Any]:
        """Read a maturity model JSON file and return it as a dictionary.

        Args:
            file_path: Absolute path to the maturity model JSON file.

        Returns:
            Parsed maturity model data as a Python dictionary.

        Raises:
            EvidenceAssessmentLoadError: If the file does not exist or contains invalid JSON.
        """
        if not file_path.exists():
            raise EvidenceAssessmentLoadError(
                f"Maturity model file not found: {file_path}"
            )

        try:
            with file_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as error:
            raise EvidenceAssessmentLoadError(
                f"Invalid JSON in maturity model file: {file_path}"
            ) from error
