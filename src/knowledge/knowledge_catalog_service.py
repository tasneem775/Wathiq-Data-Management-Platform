"""Knowledge catalog service for the NDI-Sentinel project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeCatalogLoadError(Exception):
    """Raised when the knowledge catalog file cannot be loaded."""


class KnowledgeCatalogService:
    """Unified read interface for the generated DC knowledge catalog.

    The Knowledge Map, RAG, the AI Compliance Engine, and the Dashboard
    consume the knowledge catalog exclusively through this service, rather
    than reading `data/knowledge_catalog/dc_knowledge_catalog.json` directly.

    Attributes:
        _catalog_path: Absolute path to the generated knowledge catalog file.
    """

    _RELATIVE_PATH: Path = (
        Path("data") / "knowledge_catalog" / "dc_knowledge_catalog.json"
    )

    def __init__(self, project_root: Path) -> None:
        """Args:
            project_root: Absolute path to the project root directory.
        """
        self._catalog_path = project_root / self._RELATIVE_PATH

    def load(self) -> list[dict[str, Any]]:
        """Read the knowledge catalog JSON file and return its relations.

        Returns:
            The list of MQ/level/evidence relation dictionaries.

        Raises:
            KnowledgeCatalogLoadError: If the file does not exist or contains
                invalid JSON.
        """
        if not self._catalog_path.exists():
            raise KnowledgeCatalogLoadError(
                f"Knowledge catalog file not found: {self._catalog_path}"
            )

        try:
            with self._catalog_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise KnowledgeCatalogLoadError(
                f"Invalid JSON format: {self._catalog_path}"
            ) from error

    def get_by_mq_id(self, mq_id: str) -> list[dict[str, Any]]:
        """Return all relations belonging to a given maturity question.

        Args:
            mq_id: The maturity question identifier, e.g. "DC.MQ.2".

        Returns:
            The relations whose `mq_id` matches the given value.
        """
        return [relation for relation in self.load() if relation.get("mq_id") == mq_id]

    def get_by_level(self, level_number: int) -> list[dict[str, Any]]:
        """Return all relations belonging to a given maturity level.

        Args:
            level_number: The maturity level number, e.g. 2.

        Returns:
            The relations whose `level_number` matches the given value.
        """
        return [
            relation
            for relation in self.load()
            if relation.get("level_number") == level_number
        ]

    def get_by_evidence_code(self, evidence_code: str) -> dict[str, Any] | None:
        """Return the relation matching a given evidence code.

        Args:
            evidence_code: The evidence identifier, e.g. "DC.M.6".

        Returns:
            The matching relation dictionary, or None if not found.
        """
        for relation in self.load():
            if relation.get("evidence_code") == evidence_code:
                return relation
        return None

    def get_by_domain(self, domain_code: str) -> list[dict[str, Any]]:
        """Return all relations belonging to a given domain.

        Args:
            domain_code: The domain identifier, e.g. "DC".

        Returns:
            The relations whose `domain_code` matches the given value.
        """
        return [
            relation
            for relation in self.load()
            if relation.get("domain_code") == domain_code
        ]
