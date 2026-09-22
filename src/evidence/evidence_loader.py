"""Evidence loader for the NDI-Sentinel project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EvidenceLoadError(Exception):
    """Raised when an MQ evidence JSON file cannot be loaded."""


class EvidenceLoader:
    """Reads and parses a single MQ evidence JSON file.

    Responsible solely for I/O: opening the file, decoding JSON, and
    returning the result as a Python dictionary. No validation is performed.
    """

    def load(self, file_path: Path) -> dict[str, Any]:
        """Read an MQ evidence JSON file and return it as a dictionary.

        Args:
            file_path: Absolute path to the evidence JSON file.

        Returns:
            Parsed evidence data as a Python dictionary.

        Raises:
            EvidenceLoadError: If the file does not exist or contains invalid JSON.
        """
        if not file_path.exists():
            raise EvidenceLoadError(
                f"Evidence file not found: {file_path}"
            )

        try:
            with file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise EvidenceLoadError(
                f"Invalid JSON format: {file_path}"
            ) from error
