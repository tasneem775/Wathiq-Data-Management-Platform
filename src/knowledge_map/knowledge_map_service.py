"""Knowledge map service for the NDI-Sentinel project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeMapLoadError(Exception):
    """Raised when the knowledge map file cannot be loaded."""


class KnowledgeMapService:
    """Unified read interface for the generated DC knowledge map.

    Consumers should read `data/knowledge_map/dc_knowledge_map.json`
    exclusively through this service, rather than opening the file directly.

    Attributes:
        _map_path: Absolute path to the generated knowledge map file.
    """

    _RELATIVE_PATH: Path = Path("data") / "knowledge_map" / "dc_knowledge_map.json"

    def __init__(self, project_root: Path) -> None:
        """Args:
            project_root: Absolute path to the project root directory.
        """
        self._map_path = project_root / self._RELATIVE_PATH

    def load(self) -> list[dict[str, Any]]:
        """Read the knowledge map JSON file and return its records.

        Returns:
            The list of evidence-to-reference record dictionaries.

        Raises:
            KnowledgeMapLoadError: If the file does not exist or contains
                invalid JSON.
        """
        if not self._map_path.exists():
            raise KnowledgeMapLoadError(f"Knowledge map file not found: {self._map_path}")

        try:
            with self._map_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise KnowledgeMapLoadError(f"Invalid JSON format: {self._map_path}") from error

    def get_by_evidence_code(self, evidence_code: str) -> dict[str, Any] | None:
        """Return the record matching a given evidence code.

        Args:
            evidence_code: The evidence identifier, e.g. "DC.M.6".

        Returns:
            The matching record dictionary, or None if not found.
        """
        for record in self.load():
            if record.get("evidence_code") == evidence_code:
                return record
        return None

    def get_by_mq_id(self, mq_id: str) -> list[dict[str, Any]]:
        """Return all records belonging to a given maturity question.

        Args:
            mq_id: The maturity question identifier, e.g. "DC.MQ.2".

        Returns:
            The records whose `mq_id` matches the given value.
        """
        return [record for record in self.load() if record.get("mq_id") == mq_id]

    def get_by_reference_pdf(self, reference_pdf: str) -> list[dict[str, Any]]:
        """Return all records linked to a given reference PDF.

        Args:
            reference_pdf: The PDF file name, e.g. "سياسة تصنيف البيانات.pdf".

        Returns:
            The records whose `reference_pdf` matches the given value.
        """
        return [
            record for record in self.load() if record.get("reference_pdf") == reference_pdf
        ]
